import random
import string
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import (
    Player,
    PlayerSettings,
    PlayerProgress,
    PlayerAchievement,
    Achievement,
    Level,
    Room,
    SessionMember,
    LearningEvent,
    TeacherAssignment,
)
from ..schemas import (
    PlayerCreateRequest,
    PlayerUpdateRequest,
    PlayerSettingsUpdate,
    WorkspaceSaveRequest,
    LearningEventCreateRequest,
)
from ..adaptive import compute_player_learning_summary

router = APIRouter(prefix="/api/players", tags=["players"])

DEFAULT_SKINS = ["nova_scout", "crimson_mech", "emerald_guardian", "quantum_gold"]
DEFAULT_ACCESSORIES = ["antenna_basic", "holo_visor", "radar_dish", "plasma_crown"]
DEFAULT_DECORS = ["holo_plant", "energy_fountain", "mini_drone", "core_trophy"]


def generate_player_code() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"NV-{suffix}"


def serialize_player_full(db: Session, player: Player) -> dict:
    if not player.settings:
        s = PlayerSettings(player_id=player.id)
        db.add(s)
        db.commit()
        db.refresh(player)

    progress_rows = db.query(PlayerProgress).filter(PlayerProgress.player_id == player.id).all()
    levels_by_id = {lv.id: lv for lv in db.query(Level).all()}

    progress_list = []
    for pr in progress_rows:
        lv = levels_by_id.get(pr.level_id)
        if lv:
            progress_list.append({
                "level_code": lv.level_code,
                "chapter_id": lv.chapter_id,
                "difficulty_tier": pr.difficulty_tier,
                "completed": pr.completed,
                "stars": pr.stars,
                "best_result": pr.best_result or {},
                "has_saved_workspace": bool(pr.saved_workspace),
                "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
            })

    unlocked_rows = db.query(PlayerAchievement).filter(PlayerAchievement.player_id == player.id).all()
    all_ach = db.query(Achievement).all()
    unlocked_ids = {ua.achievement_id: ua.unlocked_at for ua in unlocked_rows}

    achievements_data = []
    for a in all_ach:
        achievements_data.append({
            "achievement_code": a.achievement_code,
            "name": a.name,
            "description": a.description,
            "category": a.category,
            "reward_type": a.reward_type,
            "reward_value": a.reward_value,
            "xp_reward": a.xp_reward,
            "unlocked": a.id in unlocked_ids,
            "unlocked_at": unlocked_ids[a.id].isoformat() if a.id in unlocked_ids else None,
        })

    # Active session & teacher assignments
    sm = (
        db.query(SessionMember)
        .filter(SessionMember.player_id == player.id, SessionMember.status == "active")
        .order_by(SessionMember.joined_at.desc())
        .first()
    )
    active_session_info = None
    active_assignments = []
    if sm and sm.session:
        active_session_info = {
            "session_code": sm.session.session_code,
            "display_name": sm.session.display_name,
            "assigned_difficulty": sm.assigned_difficulty,
        }
        assign_rows = (
            db.query(TeacherAssignment)
            .filter(
                TeacherAssignment.session_id == sm.session_id,
                (TeacherAssignment.target_player_id == player.id) | (TeacherAssignment.target_player_id.is_(None)),
            )
            .order_by(TeacherAssignment.created_at.desc())
            .all()
        )
        for ar in assign_rows:
            if ar.target_player_id == player.id:
                lv = levels_by_id.get(ar.level_id)
                if lv:
                    active_assignments.append({
                        "assignment_id": ar.id,
                        "level_code": lv.level_code,
                        "level_name": lv.level_name,
                        "difficulty_tier": ar.difficulty_tier,
                        "created_at": ar.created_at.isoformat(),
                    })

    learning_summary = compute_player_learning_summary(
        db, player.id, session_id=sm.session_id if sm else None
    )

    return {
        "id": player.id,
        "player_code": player.player_code,
        "nickname": player.nickname,
        "character_skin": player.character_skin,
        "head_accessory": player.head_accessory,
        "color_theme": player.color_theme,
        "base_decor": player.base_decor,
        "title_badge": player.title_badge,
        "experience": player.experience,
        "level_rank": (player.experience // 100) + 1,
        "settings": {
            "sound_enabled": player.settings.sound_enabled,
            "animation_level": player.settings.animation_level,
            "text_size": player.settings.text_size,
        },
        "available_skins": DEFAULT_SKINS,
        "available_accessories": DEFAULT_ACCESSORIES,
        "available_decors": DEFAULT_DECORS,
        "progress": progress_list,
        "achievements": achievements_data,
        "active_session": active_session_info,
        "teacher_assignments": active_assignments,
        "learning_summary": learning_summary,
    }


@router.post("")
def create_or_get_player(req: PlayerCreateRequest, db: Session = Depends(get_db)):
    if req.player_code:
        existing = db.query(Player).filter(Player.player_code == req.player_code).first()
        if existing:
            if req.nickname and req.nickname.strip():
                existing.nickname = req.nickname.strip()[:64]
                db.commit()
                db.refresh(existing)
            return serialize_player_full(db, existing)

    code = req.player_code or generate_player_code()
    while db.query(Player).filter(Player.player_code == code).first() is not None:
        code = generate_player_code()

    nickname = (req.nickname or "").strip()
    if not nickname:
        nickname = f"修復員-{code[-4:]}"

    player = Player(
        player_code=code,
        nickname=nickname[:64],
        character_skin=req.character_skin or "nova_scout",
    )
    db.add(player)
    db.flush()

    settings_row = PlayerSettings(player_id=player.id)
    db.add(settings_row)
    db.commit()
    db.refresh(player)
    return serialize_player_full(db, player)


@router.get("/{player_code}")
def get_player(player_code: str, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.player_code == player_code).first()
    if not player:
        raise HTTPException(status_code=404, detail="找不到該玩家代號")
    return serialize_player_full(db, player)


@router.patch("/{player_code}")
def update_player(player_code: str, req: PlayerUpdateRequest, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.player_code == player_code).first()
    if not player:
        raise HTTPException(status_code=404, detail="找不到該玩家代號")

    if req.nickname is not None and req.nickname.strip():
        player.nickname = req.nickname.strip()[:64]
    if req.character_skin is not None:
        player.character_skin = req.character_skin
    if req.head_accessory is not None:
        player.head_accessory = req.head_accessory
    if req.color_theme is not None:
        player.color_theme = req.color_theme
    if req.base_decor is not None:
        player.base_decor = req.base_decor
    if req.title_badge is not None:
        player.title_badge = req.title_badge

    db.commit()
    db.refresh(player)
    return serialize_player_full(db, player)


@router.put("/{player_code}/settings")
def update_player_settings(player_code: str, req: PlayerSettingsUpdate, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.player_code == player_code).first()
    if not player:
        raise HTTPException(status_code=404, detail="找不到該玩家代號")
    if not player.settings:
        player.settings = PlayerSettings(player_id=player.id)

    if req.sound_enabled is not None:
        player.settings.sound_enabled = req.sound_enabled
    if req.animation_level in ("normal", "fast", "reduced"):
        player.settings.animation_level = req.animation_level
    if req.text_size in ("medium", "large"):
        player.settings.text_size = req.text_size

    db.commit()
    db.refresh(player)
    return serialize_player_full(db, player)


@router.post("/workspace/save")
def save_workspace(req: WorkspaceSaveRequest, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.player_code == req.player_code).first()
    if not player:
        raise HTTPException(status_code=404, detail="找不到該玩家")
    level = db.query(Level).filter(Level.level_code == req.level_code).first()
    if not level:
        raise HTTPException(status_code=404, detail="找不到該關卡")

    tier = req.difficulty_tier if req.difficulty_tier in ("guided", "core", "challenge") else "guided"
    pr = (
        db.query(PlayerProgress)
        .filter(
            PlayerProgress.player_id == player.id,
            PlayerProgress.level_id == level.id,
            PlayerProgress.difficulty_tier == tier,
        )
        .first()
    )
    payload = dict(req.workspace_data or {})
    if "version" not in payload:
        payload["version"] = 1

    if not pr:
        pr = PlayerProgress(
            player_id=player.id,
            level_id=level.id,
            difficulty_tier=tier,
            completed=False,
            stars=0,
            saved_workspace=payload,
        )
        db.add(pr)
    else:
        pr.saved_workspace = payload

    db.commit()
    return {"status": "saved", "level_code": level.level_code, "difficulty_tier": tier, "version": payload["version"]}


@router.get("/{player_code}/workspace/{level_code}")
def load_workspace(player_code: str, level_code: str, difficulty_tier: str = "guided", db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.player_code == player_code).first()
    level = db.query(Level).filter(Level.level_code == level_code).first()
    if not player or not level:
        return {"workspace_data": None}

    pr = (
        db.query(PlayerProgress)
        .filter(
            PlayerProgress.player_id == player.id,
            PlayerProgress.level_id == level.id,
            PlayerProgress.difficulty_tier == difficulty_tier,
        )
        .first()
    )
    return {
        "level_code": level_code,
        "difficulty_tier": difficulty_tier,
        "workspace_data": pr.saved_workspace if pr and pr.saved_workspace else None,
    }


@router.post("/events")
def record_learning_event(req: LearningEventCreateRequest, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.player_code == req.player_code).first()
    if not player:
        raise HTTPException(status_code=404, detail="找不到該玩家")

    level_id = None
    if req.level_code:
        lv = db.query(Level).filter(Level.level_code == req.level_code).first()
        if lv:
            level_id = lv.id

    room_id = None
    if req.room_code:
        rm = db.query(Room).filter(Room.room_code == req.room_code).first()
        if rm:
            room_id = rm.id

    sm = (
        db.query(SessionMember)
        .filter(SessionMember.player_id == player.id, SessionMember.status == "active")
        .order_by(SessionMember.joined_at.desc())
        .first()
    )

    ev = LearningEvent(
        player_id=player.id,
        room_id=room_id,
        session_id=sm.session_id if sm else None,
        level_id=level_id,
        difficulty_tier=req.difficulty_tier or "guided",
        concept_code=req.concept_code or "sequence",
        event_type=req.event_type,
        event_data=req.event_data or {},
    )
    db.add(ev)
    db.commit()
    return {"status": "recorded", "event_id": ev.id}

