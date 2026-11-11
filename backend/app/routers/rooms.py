import random
import string
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from ..database import get_db, SessionLocal
from ..models import Room, RoomMember, Player, TeachingSession
from ..schemas import RoomCreateRequest, RoomJoinRequest, RoomLeaveRequest, RoomActionRequest
from ..ws_manager import (
    ws_manager,
    recalculate_room_roles,
    rotate_room_turn,
    serialize_room_state,
    ALLOWED_QUICK_MESSAGES,
    ALLOWED_EMOJIS,
)

router = APIRouter(tags=["rooms"])


def generate_room_code() -> str:
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choices(chars, k=6))


@router.post("/api/rooms")
async def create_room(req: RoomCreateRequest, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.player_code == req.player_code).first()
    if not player:
        raise HTTPException(status_code=404, detail="找不到該玩家代號")

    code = generate_room_code()
    while db.query(Room).filter(Room.room_code == code).first() is not None:
        code = generate_room_code()

    session_id = None
    if req.session_code:
        ts = db.query(TeachingSession).filter(TeachingSession.session_code == req.session_code).first()
        if ts and ts.status == "active":
            session_id = ts.id

    room = Room(
        room_code=code,
        host_player_id=player.id,
        editor_player_id=player.id,
        session_id=session_id,
        status="playing",
        current_level=req.level_code or "ch1_lv1",
        difficulty_tier=req.difficulty_tier if req.difficulty_tier in ("guided", "core", "challenge") else "guided",
        turn_index=0,
        editor_locked=False,
        workspace_state={"version": 1, "mode": "cards", "ast": []},
        turn_history=[{
            "level_code": req.level_code or "ch1_lv1",
            "new_editor_code": player.player_code,
            "new_editor_nickname": player.nickname,
            "reason": "room_created",
        }],
    )
    db.add(room)
    db.flush()

    member = RoomMember(
        room_id=room.id,
        player_id=player.id,
        role="all_rounder",
        is_ready=True,
        is_observer=False,
        is_online=True,
    )
    db.add(member)
    recalculate_room_roles(db, room)
    db.commit()
    db.refresh(room)

    return serialize_room_state(db, room)


@router.post("/api/rooms/join")
async def join_room(req: RoomJoinRequest, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.player_code == req.player_code).first()
    if not player:
        raise HTTPException(status_code=404, detail="找不到該玩家代號")

    code = req.room_code.strip().upper()
    room = db.query(Room).filter(Room.room_code == code).first()
    if not room or room.status == "closed":
        raise HTTPException(status_code=404, detail="找不到該房間代碼或房間已關閉")

    members = db.query(RoomMember).filter(RoomMember.room_id == room.id).all()
    existing_member = next((m for m in members if m.player_id == player.id), None)

    if existing_member:
        existing_member.is_online = True
    else:
        if len(members) >= 4:
            raise HTTPException(status_code=400, detail="房間已滿（最多支援 4 位玩家合作），無法加入第 5 位玩家")
        # If program is actively executing (editor_locked), join as observer first; otherwise join active role rotation
        join_as_observer = bool(room.editor_locked)
        new_member = RoomMember(
            room_id=room.id,
            player_id=player.id,
            role="observer" if join_as_observer else "programmer",
            is_ready=True,
            is_observer=join_as_observer,
            is_online=True,
        )
        db.add(new_member)
        db.flush()

    recalculate_room_roles(db, room)
    db.commit()
    db.refresh(room)

    state = serialize_room_state(db, room)
    await ws_manager.broadcast(
        room.room_code,
        {
            "type": "player_joined",
            "player_code": player.player_code,
            "nickname": player.nickname,
            "room_state": state,
        },
    )
    return state


@router.post("/api/rooms/leave")
async def leave_room(req: RoomLeaveRequest, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.player_code == req.player_code).first()
    room = db.query(Room).filter(Room.room_code == req.room_code.strip().upper()).first()
    if not player or not room:
        return {"status": "left"}

    member = (
        db.query(RoomMember)
        .filter(RoomMember.room_id == room.id, RoomMember.player_id == player.id)
        .first()
    )
    if member:
        db.delete(member)
        db.flush()

    remaining = db.query(RoomMember).filter(RoomMember.room_id == room.id).all()
    if not remaining:
        room.status = "closed"
        room.editor_locked = False
        db.commit()
        return {"status": "room_closed"}

    if room.editor_player_id == player.id:
        room.editor_locked = False
    recalculate_room_roles(db, room)
    db.commit()
    db.refresh(room)

    state = serialize_room_state(db, room)
    await ws_manager.broadcast(
        room.room_code,
        {
            "type": "player_left",
            "player_code": player.player_code,
            "nickname": player.nickname,
            "room_state": state,
        },
    )
    return state


@router.get("/api/rooms/{room_code}")
def get_room_info(room_code: str, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.room_code == room_code.strip().upper()).first()
    if not room:
        raise HTTPException(status_code=404, detail="找不到該房間代碼")
    return serialize_room_state(db, room)


@router.post("/api/rooms/{room_code}/start")
async def start_or_change_room_level(room_code: str, req: RoomActionRequest, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.room_code == room_code.strip().upper()).first()
    if not room:
        raise HTTPException(status_code=404, detail="找不到該房間")
    player = db.query(Player).filter(Player.player_code == req.player_code).first()
    if not player:
        raise HTTPException(status_code=404, detail="找不到該玩家")

    member = (
        db.query(RoomMember)
        .filter(RoomMember.room_id == room.id, RoomMember.player_id == player.id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=403, detail="你不是此房間成員")

    room.status = "playing"
    if req.level_code:
        room.current_level = req.level_code
    if req.difficulty_tier in ("guided", "core", "challenge"):
        room.difficulty_tier = req.difficulty_tier
    room.editor_locked = False

    # Promote any observers when starting a new level
    for m in db.query(RoomMember).filter(RoomMember.room_id == room.id).all():
        m.is_observer = False
    recalculate_room_roles(db, room)

    db.commit()
    db.refresh(room)
    state = serialize_room_state(db, room)
    await ws_manager.broadcast(
        room.room_code,
        {
            "type": "game_started",
            "level_code": room.current_level,
            "difficulty_tier": room.difficulty_tier,
            "room_state": state,
        },
    )
    return state


@router.post("/api/rooms/{room_code}/rotate")
async def rotate_turn_endpoint(room_code: str, req: RoomActionRequest, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.room_code == room_code.strip().upper()).first()
    if not room:
        raise HTTPException(status_code=404, detail="找不到該房間")
    player = db.query(Player).filter(Player.player_code == req.player_code).first()
    if not player:
        raise HTTPException(status_code=404, detail="找不到該玩家")

    member = (
        db.query(RoomMember)
        .filter(RoomMember.room_id == room.id, RoomMember.player_id == player.id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=403, detail="你不是此房間成員")

    if room.editor_player_id != player.id and room.host_player_id != player.id:
        raise HTTPException(status_code=403, detail="只有目前主操作者或房主可以主動輪替操作權")

    rotate_room_turn(db, room, reason="manual_pass")
    db.commit()
    db.refresh(room)
    state = serialize_room_state(db, room)
    await ws_manager.broadcast(
        room.room_code,
        {
            "type": "turn_changed",
            "room_state": state,
        },
    )
    return state


@router.websocket("/ws/rooms/{room_code}")
async def room_websocket_endpoint(
    websocket: WebSocket,
    room_code: str,
    player_code: str = Query(...),
):
    code = room_code.strip().upper()
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.room_code == code).first()
        player = db.query(Player).filter(Player.player_code == player_code).first()
        if not room or not player:
            await websocket.close(code=4004)
            return

        member = (
            db.query(RoomMember)
            .filter(RoomMember.room_id == room.id, RoomMember.player_id == player.id)
            .first()
        )
        if not member:
            await websocket.close(code=4003)
            return

        member.is_online = True
        recalculate_room_roles(db, room)
        db.commit()
        db.refresh(room)
        initial_state = serialize_room_state(db, room)
    finally:
        db.close()

    await ws_manager.connect(code, player_code, websocket)
    await ws_manager.broadcast(
        code,
        {
            "type": "room_state",
            "room_state": initial_state,
        },
    )

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            db = SessionLocal()
            try:
                room = db.query(Room).filter(Room.room_code == code).first()
                player = db.query(Player).filter(Player.player_code == player_code).first()
                if not room or not player:
                    break

                is_editor = (room.editor_player_id == player.id) or (
                    db.query(RoomMember).filter(RoomMember.room_id == room.id).count() <= 1
                )

                if msg_type == "editor_state_updated":
                    if is_editor and not room.editor_locked:
                        ws_state = data.get("workspace_state", {})
                        room.workspace_state = ws_state
                        db.commit()
                        await ws_manager.broadcast(
                            code,
                            {
                                "type": "editor_state_updated",
                                "updated_by": player_code,
                                "workspace_state": ws_state,
                            },
                        )

                elif msg_type == "editor_lock_changed":
                    if is_editor:
                        room.editor_locked = bool(data.get("locked", False))
                        db.commit()
                        await ws_manager.broadcast(
                            code,
                            {
                                "type": "editor_lock_changed",
                                "locked": room.editor_locked,
                                "editor_player_code": player_code,
                            },
                        )

                elif msg_type == "robot_action":
                    if is_editor:
                        await ws_manager.broadcast(
                            code,
                            {
                                "type": "robot_action",
                                "action_data": data.get("action_data", {}),
                                "triggered_by": player_code,
                            },
                        )

                elif msg_type == "quick_message":
                    msg_key = data.get("message_key", "")
                    emoji = data.get("emoji", "")
                    if msg_key in ALLOWED_QUICK_MESSAGES:
                        text = ALLOWED_QUICK_MESSAGES[msg_key]
                        if msg_key == "pass_turn" and is_editor:
                            rotate_room_turn(db, room, reason="quick_message_pass")
                            db.commit()
                            db.refresh(room)
                            await ws_manager.broadcast(
                                code,
                                {
                                    "type": "turn_changed",
                                    "room_state": serialize_room_state(db, room),
                                },
                            )
                        await ws_manager.broadcast(
                            code,
                            {
                                "type": "quick_message",
                                "player_code": player_code,
                                "nickname": player.nickname,
                                "message_key": msg_key,
                                "text": text,
                            },
                        )
                    elif emoji in ALLOWED_EMOJIS:
                        await ws_manager.broadcast(
                            code,
                            {
                                "type": "quick_message",
                                "player_code": player_code,
                                "nickname": player.nickname,
                                "emoji": emoji,
                                "text": emoji,
                            },
                        )
            finally:
                db.close()

    except WebSocketDisconnect:
        ws_manager.disconnect(code, player_code)
        db = SessionLocal()
        try:
            room = db.query(Room).filter(Room.room_code == code).first()
            player = db.query(Player).filter(Player.player_code == player_code).first()
            if room and player:
                member = (
                    db.query(RoomMember)
                    .filter(RoomMember.room_id == room.id, RoomMember.player_id == player.id)
                    .first()
                )
                if member:
                    member.is_online = False
                if room.editor_player_id == player.id:
                    room.editor_locked = False
                    # Hand off editor control to next online member if available
                    online_others = (
                        db.query(RoomMember)
                        .filter(
                            RoomMember.room_id == room.id,
                            RoomMember.is_online == True,
                            RoomMember.player_id != player.id,
                        )
                        .all()
                    )
                    if online_others:
                        room.editor_player_id = online_others[0].player_id
                recalculate_room_roles(db, room)
                db.commit()
                db.refresh(room)
                await ws_manager.broadcast(
                    code,
                    {
                        "type": "player_left",
                        "player_code": player_code,
                        "disconnected": True,
                        "room_state": serialize_room_state(db, room),
                    },
                )
        finally:
            db.close()

