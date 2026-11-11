from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import (
    Level,
    LevelVariant,
    Player,
    PlayerProgress,
    MissionRecord,
    Achievement,
    PlayerAchievement,
    LearningEvent,
    Room,
    RoomMember,
    SessionMember,
)
from ..schemas import ProgramSubmitRequest
from ..engine_validator import simulate_program
from ..ws_manager import rotate_room_turn, serialize_room_state, ws_manager
from ..adaptive import compute_player_learning_summary

router = APIRouter(prefix="/api/levels", tags=["levels"])


@router.get("")
def list_levels(db: Session = Depends(get_db)):
    levels = db.query(Level).order_by(Level.level_order.asc()).all()
    result = []
    for lv in levels:
        variants = db.query(LevelVariant).filter(LevelVariant.level_id == lv.id, LevelVariant.is_active == True).all()
        tiers = {v.difficulty_tier: v.level_data for v in variants}
        result.append({
            "id": lv.id,
            "level_code": lv.level_code,
            "chapter_id": lv.chapter_id,
            "chapter_name": lv.chapter_name,
            "level_order": lv.level_order,
            "level_name": lv.level_name,
            "description": lv.description,
            "difficulty": lv.difficulty,
            "learning_objective": lv.learning_objective,
            "concept_code": lv.concept_code,
            "editor_mode": lv.editor_mode,
            "available_tiers": list(tiers.keys()),
            "variants": tiers,
        })
    return {"levels": result}


@router.get("/{level_code}")
def get_level_detail(level_code: str, difficulty_tier: str = "guided", db: Session = Depends(get_db)):
    lv = db.query(Level).filter(Level.level_code == level_code).first()
    if not lv:
        raise HTTPException(status_code=404, detail="找不到指定關卡")

    variants = db.query(LevelVariant).filter(LevelVariant.level_id == lv.id, LevelVariant.is_active == True).all()
    tiers_map = {v.difficulty_tier: v.level_data for v in variants}
    selected_tier = difficulty_tier if difficulty_tier in tiers_map else "guided"
    active_data = tiers_map.get(selected_tier) or lv.level_data

    return {
        "id": lv.id,
        "level_code": lv.level_code,
        "chapter_id": lv.chapter_id,
        "chapter_name": lv.chapter_name,
        "level_order": lv.level_order,
        "level_name": lv.level_name,
        "description": lv.description,
        "learning_objective": lv.learning_objective,
        "concept_code": lv.concept_code,
        "editor_mode": lv.editor_mode,
        "selected_tier": selected_tier,
        "level_data": active_data,
        "variants": tiers_map,
    }


def check_and_unlock_achievements(
    db: Session,
    player: Player,
    level: Level,
    difficulty_tier: str,
    concepts_used: list[str],
    had_prior_error: bool,
    is_coop: bool,
    bonus_energy: int = 0,
) -> list[dict]:
    all_ach = {a.achievement_code: a for a in db.query(Achievement).all()}
    existing_ids = {
        pa.achievement_id
        for pa in db.query(PlayerAchievement).filter(PlayerAchievement.player_id == player.id).all()
    }

    codes_to_unlock = set()
    codes_to_unlock.add("first_boot")

    if "loops" in concepts_used or level.concept_code == "loops":
        codes_to_unlock.add("junior_engineer")
    if "conditions" in concepts_used or level.concept_code == "conditions":
        codes_to_unlock.add("logic_master")
    if "variables" in concepts_used or level.concept_code == "variables":
        codes_to_unlock.add("resource_commander")
    if "logic" in concepts_used or level.concept_code == "logic":
        codes_to_unlock.add("dual_core_sync")
    if "functions" in concepts_used or level.concept_code == "functions":
        codes_to_unlock.add("automation_expert")
    if had_prior_error:
        codes_to_unlock.add("debug_specialist")
    if is_coop:
        codes_to_unlock.add("best_teammate")
    if difficulty_tier == "challenge":
        codes_to_unlock.add("challenge_explorer")
    if bonus_energy > 0 or level.level_code == "ch7_lv1":
        codes_to_unlock.add("secret_finder")
    if level.chapter_id >= 7:
        codes_to_unlock.add("nova_savior")

    newly_unlocked = []
    for code in codes_to_unlock:
        ach = all_ach.get(code)
        if ach and ach.id not in existing_ids:
            db.add(PlayerAchievement(player_id=player.id, achievement_id=ach.id))
            player.experience += ach.xp_reward
            if ach.reward_type == "title" and ach.reward_value:
                player.title_badge = ach.reward_value
            newly_unlocked.append({
                "achievement_code": ach.achievement_code,
                "name": ach.name,
                "description": ach.description,
                "reward_type": ach.reward_type,
                "reward_value": ach.reward_value,
                "xp_reward": ach.xp_reward,
            })

    return newly_unlocked


@router.post("/{level_code}/submit")
async def submit_level_program(level_code: str, req: ProgramSubmitRequest, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.player_code == req.player_code).first()
    if not player:
        raise HTTPException(status_code=404, detail="找不到該玩家代號")

    level = db.query(Level).filter(Level.level_code == level_code).first()
    if not level:
        raise HTTPException(status_code=404, detail="找不到指定關卡")

    tier = req.difficulty_tier if req.difficulty_tier in ("guided", "core", "challenge") else "guided"
    variant = (
        db.query(LevelVariant)
        .filter(LevelVariant.level_id == level.id, LevelVariant.difficulty_tier == tier)
        .first()
    )
    level_data = variant.level_data if variant else level.level_data

    # Verify room membership & editor permission if in a room
    room = None
    room_members = []
    if req.room_code:
        room = db.query(Room).filter(Room.room_code == req.room_code).first()
        if not room:
            raise HTTPException(status_code=404, detail="找不到指定房間")
        room_members = db.query(RoomMember).filter(RoomMember.room_id == room.id).all()
        member_ids = {m.player_id for m in room_members}
        if player.id not in member_ids:
            raise HTTPException(status_code=403, detail="你不是此房間的成員，無法提交程式")
        if room.editor_player_id and room.editor_player_id != player.id and len(room_members) > 1:
            raise HTTPException(status_code=403, detail="目前由隊友持有主要編輯權，請由主操作者執行提交")

    # Run safe server-side execution engine verification
    sim_result = simulate_program(req.program_ast, level_data)

    sm = (
        db.query(SessionMember)
        .filter(SessionMember.player_id == player.id, SessionMember.status == "active")
        .order_by(SessionMember.joined_at.desc())
        .first()
    )
    session_id = sm.session_id if sm else (room.session_id if room else None)

    # Record program_run event
    db.add(
        LearningEvent(
            player_id=player.id,
            room_id=room.id if room else None,
            session_id=session_id,
            level_id=level.id,
            difficulty_tier=tier,
            concept_code=level.concept_code,
            event_type="program_run",
            event_data={
                "success": sim_result["success"],
                "steps_taken": sim_result.get("steps_taken", 0),
                "concepts_used": sim_result.get("concepts_used", []),
            },
        )
    )

    if not sim_result["success"]:
        db.add(
            LearningEvent(
                player_id=player.id,
                room_id=room.id if room else None,
                session_id=session_id,
                level_id=level.id,
                difficulty_tier=tier,
                concept_code=level.concept_code,
                event_type="error_occurred",
                event_data={
                    "error_type": sim_result.get("error_type"),
                    "error_step": sim_result.get("error_step"),
                    "message": sim_result.get("message"),
                },
            )
        )
        db.commit()
        return {
            "verified": False,
            "simulation": sim_result,
            "xp_gained": 0,
            "newly_unlocked_achievements": [],
        }

    # Check if player previously had an error on this level (for self_corrected learning evidence!)
    prior_error = (
        db.query(LearningEvent)
        .filter(
            LearningEvent.player_id == player.id,
            LearningEvent.level_id == level.id,
            LearningEvent.event_type == "error_occurred",
        )
        .first()
    )
    if prior_error:
        db.add(
            LearningEvent(
                player_id=player.id,
                room_id=room.id if room else None,
                session_id=session_id,
                level_id=level.id,
                difficulty_tier=tier,
                concept_code=level.concept_code,
                event_type="self_corrected",
                event_data={"corrected_from": prior_error.event_data.get("error_type")},
            )
        )

    db.add(
        LearningEvent(
            player_id=player.id,
            room_id=room.id if room else None,
            session_id=session_id,
            level_id=level.id,
            difficulty_tier=tier,
            concept_code=level.concept_code,
            event_type="level_completed",
            event_data={
                "hints_used": req.hints_used,
                "attempts": req.attempts,
                "concepts_used": sim_result.get("concepts_used", []),
                "reflection_answer": req.reflection_answer,
            },
        )
    )

    # Encouraging star & XP system: never penalizes hint usage or slower completion time!
    stars = 3
    base_xp = {"guided": 40, "core": 60, "challenge": 90}.get(tier, 50)
    if prior_error:
        base_xp += 15  # Bonus XP for resilience & debugging!

    target_players = [player]
    if room and len(room_members) > 1:
        member_player_ids = [m.player_id for m in room_members]
        target_players = db.query(Player).filter(Player.id.in_(member_player_ids)).all()

    all_new_achievements = []
    for p in target_players:
        p.experience += base_xp
        pr = (
            db.query(PlayerProgress)
            .filter(
                PlayerProgress.player_id == p.id,
                PlayerProgress.level_id == level.id,
                PlayerProgress.difficulty_tier == tier,
            )
            .first()
        )
        best_res = {
            "steps_taken": sim_result.get("steps_taken", 0),
            "node_count": sim_result.get("node_count", 0),
            "concepts_used": sim_result.get("concepts_used", []),
            "self_corrected": bool(prior_error),
        }
        if not pr:
            pr = PlayerProgress(
                player_id=p.id,
                level_id=level.id,
                difficulty_tier=tier,
                completed=True,
                stars=stars,
                best_result=best_res,
                saved_workspace=req.workspace_data or {},
            )
            db.add(pr)
        else:
            pr.completed = True
            pr.stars = max(pr.stars, stars)
            pr.best_result = best_res
            if req.workspace_data:
                pr.saved_workspace = req.workspace_data

        unlocked = check_and_unlock_achievements(
            db=db,
            player=p,
            level=level,
            difficulty_tier=tier,
            concepts_used=sim_result.get("concepts_used", []),
            had_prior_error=bool(prior_error),
            is_coop=bool(room and len(room_members) > 1),
            bonus_energy=int(sim_result.get("bonus_energy", 0)),
        )
        if p.id == player.id:
            all_new_achievements = unlocked

    role_dist = {}
    if room:
        for m in room_members:
            if m.player:
                role_dist[m.player.player_code] = m.role

    db.add(
        MissionRecord(
            room_id=room.id if room else None,
            player_id=player.id,
            level_id=level.id,
            difficulty_tier=tier,
            completed=True,
            attempts=max(1, req.attempts),
            hints_used=max(0, req.hints_used),
            completion_time=max(0, req.completion_time),
            role_distribution=role_dist,
        )
    )

    updated_room_state = None
    if room:
        rotate_room_turn(db, room, reason=f"completed_{level.level_code}")
        db.commit()
        db.refresh(room)
        updated_room_state = serialize_room_state(db, room)
        await ws_manager.broadcast(
            room.room_code,
            {
                "type": "mission_completed",
                "level_code": level.level_code,
                "difficulty_tier": tier,
                "submitted_by": player.nickname,
                "room_state": updated_room_state,
            },
        )
    else:
        db.commit()

    learning_summary = compute_player_learning_summary(db, player.id, session_id=session_id)

    return {
        "verified": True,
        "simulation": sim_result,
        "stars": stars,
        "xp_gained": base_xp,
        "total_xp": player.experience,
        "self_corrected_bonus": bool(prior_error),
        "newly_unlocked_achievements": all_new_achievements,
        "room_state": updated_room_state,
        "learning_summary": learning_summary,
    }

