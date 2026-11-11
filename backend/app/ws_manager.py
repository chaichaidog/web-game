from typing import Any
from datetime import datetime, timezone
from fastapi import WebSocket
from sqlalchemy.orm import Session
from .models import Room, RoomMember, Player

ALLOWED_QUICK_MESSAGES = {
    "idea": "💡 我有一個想法！",
    "try_again": "🔄 沒關係，我們再試一次！",
    "check_here": "🔍 這裡的指令順序可能有問題喔！",
    "use_loop": "🔁 這段動作重複出現，要不要試試看迴圈？",
    "watch_obstacle": "⚠️ 注意前方有障礙物，記得先轉彎！",
    "check_energy": "⚡ 記得先到能源晶片格子上執行「撿取能源」！",
    "good_job": "🎉 太棒了！我們離通關越來越近了！",
    "pass_turn": "🤝 我先把操作權交給下一位隊友試試看！",
}

ALLOWED_EMOJIS = {"👍", "💡", "⚡", "🤖", "🎉", "🔍", "❤️"}

ROLE_LABELS = {
    "all_rounder": "全能修復員（分析／編排／測試／除錯）",
    "programmer_tester": "程式編排＆測試員（主操作）",
    "map_strategist": "地圖分析＆策略員",
    "programmer": "程式編排員（主操作）",
    "map_analyst": "地圖分析員",
    "tester_debugger": "測試＆除錯員",
    "tester": "執行測試員",
    "debugger": "邏輯除錯員",
    "observer": "觀察見習員（下一關納入輪替）",
}


def recalculate_room_roles(db: Session, room: Room) -> None:
    """
    Dynamically assigns roles for 1~4 players and ensures a valid active editor_player_id.
    """
    members = (
        db.query(RoomMember)
        .filter(RoomMember.room_id == room.id)
        .order_by(RoomMember.joined_at.asc(), RoomMember.id.asc())
        .all()
    )
    if not members:
        room.editor_player_id = None
        room.host_player_id = None
        db.flush()
        return

    online_members = [m for m in members if m.is_online]
    active_pool = online_members if online_members else members

    # Ensure host_player_id is valid and online if possible
    if room.host_player_id not in [m.player_id for m in active_pool]:
        room.host_player_id = active_pool[0].player_id

    # Eligible editors (non-observers first; if all are observers, promote them)
    non_observer_pool = [m for m in active_pool if not m.is_observer]
    if not non_observer_pool:
        for m in active_pool:
            m.is_observer = False
        non_observer_pool = active_pool

    if room.editor_player_id not in [m.player_id for m in non_observer_pool]:
        idx = room.turn_index % len(non_observer_pool)
        room.editor_player_id = non_observer_pool[idx].player_id

    # Find editor position in non_observer_pool
    editor_idx = next(
        (i for i, m in enumerate(non_observer_pool) if m.player_id == room.editor_player_id),
        0,
    )
    ordered = non_observer_pool[editor_idx:] + non_observer_pool[:editor_idx]
    n = len(ordered)

    if n == 1:
        ordered[0].role = "all_rounder"
    elif n == 2:
        ordered[0].role = "programmer_tester"
        ordered[1].role = "map_strategist"
    elif n == 3:
        ordered[0].role = "programmer"
        ordered[1].role = "map_analyst"
        ordered[2].role = "tester_debugger"
    else:
        ordered[0].role = "programmer"
        ordered[1].role = "map_analyst"
        ordered[2].role = "tester"
        for extra in ordered[3:]:
            extra.role = "debugger"

    for m in members:
        if m.is_observer:
            m.role = "observer"

    db.flush()


def rotate_room_turn(db: Session, room: Room, reason: str = "level_completed") -> None:
    """
    Rotates the primary editor role to the next member in the room and promotes any mid-level observers.
    """
    members = (
        db.query(RoomMember)
        .filter(RoomMember.room_id == room.id)
        .order_by(RoomMember.joined_at.asc(), RoomMember.id.asc())
        .all()
    )
    if not members:
        return

    for m in members:
        if m.is_observer:
            m.is_observer = False

    online_members = [m for m in members if m.is_online] or members
    room.turn_index = (room.turn_index + 1) % len(online_members)
    room.editor_player_id = online_members[room.turn_index].player_id
    room.editor_locked = False
    recalculate_room_roles(db, room)

    history = list(room.turn_history or [])
    editor_player = db.query(Player).filter(Player.id == room.editor_player_id).first()
    history.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level_code": room.current_level,
        "new_editor_code": editor_player.player_code if editor_player else None,
        "new_editor_nickname": editor_player.nickname if editor_player else None,
        "reason": reason,
    })
    room.turn_history = history[-50:]
    db.flush()


def serialize_room_state(db: Session, room: Room) -> dict[str, Any]:
    members = (
        db.query(RoomMember)
        .filter(RoomMember.room_id == room.id)
        .order_by(RoomMember.joined_at.asc(), RoomMember.id.asc())
        .all()
    )
    member_list = []
    host_code = None
    editor_code = None
    for m in members:
        p = m.player
        if not p:
            continue
        if p.id == room.host_player_id:
            host_code = p.player_code
        if p.id == room.editor_player_id:
            editor_code = p.player_code
        member_list.append({
            "player_id": p.id,
            "player_code": p.player_code,
            "nickname": p.nickname,
            "character_skin": p.character_skin,
            "head_accessory": p.head_accessory,
            "role": m.role,
            "role_label": ROLE_LABELS.get(m.role, m.role),
            "is_ready": m.is_ready,
            "is_observer": m.is_observer,
            "is_online": m.is_online,
            "is_host": p.id == room.host_player_id,
            "is_editor": p.id == room.editor_player_id,
        })

    return {
        "room_id": room.id,
        "room_code": room.room_code,
        "status": room.status,
        "current_level": room.current_level,
        "difficulty_tier": room.difficulty_tier,
        "host_player_code": host_code,
        "editor_player_code": editor_code,
        "editor_locked": room.editor_locked,
        "turn_index": room.turn_index,
        "player_count": len(member_list),
        "is_solo": len(member_list) <= 1,
        "members": member_list,
        "workspace_state": room.workspace_state or {},
        "turn_history": room.turn_history or [],
    }


class ConnectionManager:
    def __init__(self):
        # room_code -> { player_code: WebSocket }
        self.active_connections: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, room_code: str, player_code: str, websocket: WebSocket):
        await websocket.accept()
        if room_code not in self.active_connections:
            self.active_connections[room_code] = {}
        self.active_connections[room_code][player_code] = websocket

    def disconnect(self, room_code: str, player_code: str):
        if room_code in self.active_connections:
            self.active_connections[room_code].pop(player_code, None)
            if not self.active_connections[room_code]:
                del self.active_connections[room_code]

    async def broadcast(self, room_code: str, message: dict[str, Any]):
        conns = list(self.active_connections.get(room_code, {}).items())
        for p_code, ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(room_code, p_code)


ws_manager = ConnectionManager()

