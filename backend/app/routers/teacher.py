import hashlib
import hmac
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from ..config import settings
from ..database import get_db
from ..models import (
    Teacher,
    TeachingSession,
    SessionMember,
    Player,
    PlayerProgress,
    Level,
    Room,
    RoomMember,
    MissionRecord,
    LearningEvent,
    TeacherAssignment,
)
from ..schemas import (
    TeacherLoginRequest,
    SessionCreateRequest,
    SessionJoinRequest,
    AssignmentCreateRequest,
    DifficultyOverrideRequest,
)
from ..adaptive import compute_player_learning_summary
from ..ws_manager import serialize_room_state

router = APIRouter(tags=["teacher"])


def create_teacher_token(teacher_id: int, auth_subject: str) -> str:
    payload = f"{teacher_id}:{auth_subject}"
    sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"


def get_current_teacher(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Teacher:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="請先登入教師管理端（缺少有效授權憑證）")
    token = authorization.replace("Bearer ", "", 1).strip()
    parts = token.split(":")
    if len(parts) != 3:
        raise HTTPException(status_code=401, detail="無效的教師授權憑證格式")
    t_id_str, subject, sig = parts
    expected_payload = f"{t_id_str}:{subject}"
    expected_sig = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        expected_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        raise HTTPException(status_code=401, detail="教師授權憑證簽章驗證失敗")

    teacher = db.query(Teacher).filter(Teacher.id == int(t_id_str), Teacher.auth_subject == subject).first()
    if not teacher:
        raise HTTPException(status_code=401, detail="找不到對應的教師帳號")
    return teacher


def generate_session_code() -> str:
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "CLS-" + "".join(random.choices(chars, k=5))


@router.post("/api/teacher/login")
def teacher_login(req: TeacherLoginRequest, db: Session = Depends(get_db)):
    if not req.passkey or not req.passkey.strip():
        raise HTTPException(status_code=401, detail="請輸入教師通行密鑰")

    # Allow the configured teacher passkey or custom teacher account passkey format "TEACHER:<subject>:<key>"
    raw_key = req.passkey.strip()
    if raw_key == settings.TEACHER_DEMO_PASSKEY:
        subject = "teacher_default"
    elif raw_key.startswith("TEACHER-"):
        subject = f"teacher_{hashlib.sha256(raw_key.encode('utf-8')).hexdigest()[:10]}"
    else:
        raise HTTPException(status_code=401, detail="教師通行密鑰錯誤（預設教學密鑰請見環境設定）")

    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    teacher = db.query(Teacher).filter(Teacher.auth_subject == subject).first()
    if not teacher:
        teacher = Teacher(
            auth_subject=subject,
            display_name=req.display_name or "資訊科技教師",
            token_hash=key_hash,
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
    elif req.display_name:
        teacher.display_name = req.display_name[:64]
        db.commit()

    token = create_teacher_token(teacher.id, teacher.auth_subject)
    return {
        "teacher_id": teacher.id,
        "display_name": teacher.display_name,
        "auth_subject": teacher.auth_subject,
        "access_token": token,
    }


@router.post("/api/teacher/sessions")
def create_teaching_session(
    req: SessionCreateRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    code = generate_session_code()
    while db.query(TeachingSession).filter(TeachingSession.session_code == code).first() is not None:
        code = generate_session_code()

    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=max(1, min(req.expires_hours, 720)))

    ts = TeachingSession(
        session_code=code,
        teacher_id=teacher.id,
        display_name=req.display_name.strip() or "NOVA 資訊課堂場次",
        created_at=now,
        expires_at=expires,
        status="active",
    )
    db.add(ts)
    db.commit()
    db.refresh(ts)

    return {
        "id": ts.id,
        "session_code": ts.session_code,
        "display_name": ts.display_name,
        "status": ts.status,
        "created_at": ts.created_at.isoformat(),
        "expires_at": ts.expires_at.isoformat() if ts.expires_at else None,
    }


@router.get("/api/teacher/sessions")
def list_teacher_sessions(
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    sessions = (
        db.query(TeachingSession)
        .filter(TeachingSession.teacher_id == teacher.id)
        .order_by(TeachingSession.created_at.desc())
        .all()
    )
    result = []
    for s in sessions:
        m_count = db.query(SessionMember).filter(SessionMember.session_id == s.id).count()
        result.append({
            "id": s.id,
            "session_code": s.session_code,
            "display_name": s.display_name,
            "status": s.status,
            "student_count": m_count,
            "created_at": s.created_at.isoformat(),
            "expires_at": s.expires_at.isoformat() if s.expires_at else None,
        })
    return {"sessions": result}


def get_authorized_session(db: Session, session_code: str, teacher: Teacher) -> TeachingSession:
    ts = db.query(TeachingSession).filter(TeachingSession.session_code == session_code.strip().upper()).first()
    if not ts:
        raise HTTPException(status_code=404, detail="找不到該教學場次代碼")
    if ts.teacher_id != teacher.id:
        raise HTTPException(status_code=403, detail="權限不足：您只能查看與管理自己建立的教學場次")
    return ts


@router.patch("/api/teacher/sessions/{session_code}")
def update_session_status(
    session_code: str,
    status: str = "closed",
    extend_hours: int = 0,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    ts = get_authorized_session(db, session_code, teacher)
    if status in ("active", "closed"):
        ts.status = status
    if extend_hours > 0:
        base_time = ts.expires_at or datetime.now(timezone.utc)
        ts.expires_at = base_time + timedelta(hours=extend_hours)
        ts.status = "active"
    db.commit()
    db.refresh(ts)
    return {
        "session_code": ts.session_code,
        "display_name": ts.display_name,
        "status": ts.status,
        "expires_at": ts.expires_at.isoformat() if ts.expires_at else None,
    }


@router.post("/api/sessions/join")
def student_join_session(req: SessionJoinRequest, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.player_code == req.player_code).first()
    if not player:
        raise HTTPException(status_code=404, detail="找不到該學生代號")

    code = req.session_code.strip().upper()
    ts = db.query(TeachingSession).filter(TeachingSession.session_code == code).first()
    if not ts:
        raise HTTPException(status_code=404, detail="找不到該課堂場次代碼")
    if ts.status != "active":
        raise HTTPException(status_code=400, detail="該課堂場次已關閉，無法加入新成員")
    if ts.expires_at and ts.expires_at < datetime.now(timezone.utc):
        ts.status = "expired"
        db.commit()
        raise HTTPException(status_code=400, detail="該課堂場次已過期")

    sm = (
        db.query(SessionMember)
        .filter(SessionMember.session_id == ts.id, SessionMember.player_id == player.id)
        .first()
    )
    if not sm:
        sm = SessionMember(
            session_id=ts.id,
            player_id=player.id,
            status="active",
        )
        db.add(sm)
    else:
        sm.status = "active"

    db.commit()
    return {
        "session_code": ts.session_code,
        "display_name": ts.display_name,
        "player_code": player.player_code,
        "nickname": player.nickname,
        "assigned_difficulty": sm.assigned_difficulty,
    }


@router.get("/api/teacher/sessions/{session_code}/overview")
def get_session_overview(
    session_code: str,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    ts = get_authorized_session(db, session_code, teacher)
    members = db.query(SessionMember).filter(SessionMember.session_id == ts.id).all()
    levels_by_id = {lv.id: lv for lv in db.query(Level).all()}

    student_list = []
    for sm in members:
        p = sm.player
        if not p:
            continue
        p_progress = db.query(PlayerProgress).filter(PlayerProgress.player_id == p.id, PlayerProgress.completed == True).all()
        completed_codes = []
        highest_chapter = 1
        tiers_used = set()
        for pr in p_progress:
            lv = levels_by_id.get(pr.level_id)
            if lv:
                completed_codes.append(f"{lv.level_code}({pr.difficulty_tier})")
                highest_chapter = max(highest_chapter, lv.chapter_id)
                tiers_used.add(pr.difficulty_tier)

        summary = compute_player_learning_summary(db, p.id, session_id=ts.id)
        student_list.append({
            "player_id": p.id,
            "player_code": p.player_code,
            "nickname": p.nickname,
            "highest_chapter": highest_chapter,
            "completed_count": len(p_progress),
            "completed_levels": completed_codes,
            "tiers_used": sorted(list(tiers_used)),
            "assigned_difficulty": sm.assigned_difficulty,
            "concepts_seen": summary["concepts_seen"],
            "total_runs": summary["total_runs"],
            "hints_used_total": summary["hints_used_total"],
            "self_corrections": summary["self_corrections"],
            "error_breakdown": summary["error_breakdown"],
            "descriptive_summary": summary["descriptive_summary"],
            "recommendations": summary["recommendations"],
        })

    # Rooms associated with this session or its members
    member_player_ids = [sm.player_id for sm in members]
    room_ids = set()
    for rm in db.query(Room).filter(Room.session_id == ts.id).all():
        room_ids.add(rm.id)
    if member_player_ids:
        for rmem in db.query(RoomMember).filter(RoomMember.player_id.in_(member_player_ids)).all():
            room_ids.add(rmem.room_id)

    rooms_data = []
    coop_records = []
    if room_ids:
        rooms = db.query(Room).filter(Room.id.in_(room_ids)).all()
        for r in rooms:
            r_state = serialize_room_state(db, r)
            rooms_data.append(r_state)
            records = db.query(MissionRecord).filter(MissionRecord.room_id == r.id).order_by(MissionRecord.created_at.desc()).all()
            for rec in records:
                lv = levels_by_id.get(rec.level_id)
                coop_records.append({
                    "room_code": r.room_code,
                    "level_code": lv.level_code if lv else "unknown",
                    "level_name": lv.level_name if lv else "",
                    "difficulty_tier": rec.difficulty_tier,
                    "attempts": rec.attempts,
                    "hints_used": rec.hints_used,
                    "role_distribution": rec.role_distribution,
                    "created_at": rec.created_at.isoformat(),
                })

    assignments = (
        db.query(TeacherAssignment)
        .filter(TeacherAssignment.session_id == ts.id)
        .order_by(TeacherAssignment.created_at.desc())
        .all()
    )
    assignments_data = []
    for ar in assignments:
        lv = levels_by_id.get(ar.level_id)
        target_p = db.query(Player).filter(Player.id == ar.target_player_id).first() if ar.target_player_id else None
        target_r = db.query(Room).filter(Room.id == ar.target_room_id).first() if ar.target_room_id else None
        assignments_data.append({
            "id": ar.id,
            "target_type": "player" if target_p else "room",
            "target_code": target_p.player_code if target_p else (target_r.room_code if target_r else ""),
            "target_name": target_p.nickname if target_p else (f"房間 {target_r.room_code}" if target_r else ""),
            "level_code": lv.level_code if lv else "",
            "level_name": lv.level_name if lv else "",
            "difficulty_tier": ar.difficulty_tier,
            "created_at": ar.created_at.isoformat(),
        })

    return {
        "session": {
            "id": ts.id,
            "session_code": ts.session_code,
            "display_name": ts.display_name,
            "status": ts.status,
            "created_at": ts.created_at.isoformat(),
            "expires_at": ts.expires_at.isoformat() if ts.expires_at else None,
        },
        "student_count": len(student_list),
        "students": student_list,
        "rooms": rooms_data,
        "coop_records": coop_records,
        "assignments": assignments_data,
    }


@router.get("/api/teacher/sessions/{session_code}/students/{player_code}")
def get_student_learning_detail(
    session_code: str,
    player_code: str,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    ts = get_authorized_session(db, session_code, teacher)
    player = db.query(Player).filter(Player.player_code == player_code).first()
    if not player:
        raise HTTPException(status_code=404, detail="找不到該學生代號")

    sm = (
        db.query(SessionMember)
        .filter(SessionMember.session_id == ts.id, SessionMember.player_id == player.id)
        .first()
    )
    if not sm:
        raise HTTPException(status_code=403, detail="該學生不屬於此教學場次")

    summary = compute_player_learning_summary(db, player.id, session_id=ts.id)
    events = (
        db.query(LearningEvent)
        .filter(LearningEvent.player_id == player.id)
        .order_by(LearningEvent.created_at.desc())
        .limit(50)
        .all()
    )
    levels_by_id = {lv.id: lv for lv in db.query(Level).all()}

    event_log = []
    for ev in events:
        lv = levels_by_id.get(ev.level_id) if ev.level_id else None
        event_log.append({
            "id": ev.id,
            "level_code": lv.level_code if lv else None,
            "difficulty_tier": ev.difficulty_tier,
            "concept_code": ev.concept_code,
            "event_type": ev.event_type,
            "event_data": ev.event_data,
            "created_at": ev.created_at.isoformat(),
        })

    return {
        "player_code": player.player_code,
        "nickname": player.nickname,
        "assigned_difficulty": sm.assigned_difficulty,
        "summary": summary,
        "recent_events": event_log,
    }


@router.post("/api/teacher/sessions/{session_code}/assign")
def create_teacher_assignment(
    session_code: str,
    req: AssignmentCreateRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    ts = get_authorized_session(db, session_code, teacher)
    if bool(req.target_player_code) == bool(req.target_room_code):
        raise HTTPException(status_code=400, detail="請明確指定「單一學生代號」或「單一房間代碼」其中之一（不可同時為空或同時指定）")

    level = db.query(Level).filter(Level.level_code == req.level_code).first()
    if not level:
        raise HTTPException(status_code=404, detail="找不到指定的關卡代碼")

    tier = req.difficulty_tier if req.difficulty_tier in ("guided", "core", "challenge") else "core"
    target_player_id = None
    target_room_id = None

    if req.target_player_code:
        player = db.query(Player).filter(Player.player_code == req.target_player_code.strip()).first()
        if not player:
            raise HTTPException(status_code=404, detail="找不到目標學生代號")
        target_player_id = player.id
        sm = (
            db.query(SessionMember)
            .filter(SessionMember.session_id == ts.id, SessionMember.player_id == player.id)
            .first()
        )
        if sm:
            sm.assigned_difficulty = tier
    else:
        room = db.query(Room).filter(Room.room_code == req.target_room_code.strip().upper()).first()
        if not room:
            raise HTTPException(status_code=404, detail="找不到目標房間代碼")
        target_room_id = room.id
        room.current_level = level.level_code
        room.difficulty_tier = tier

    assignment = TeacherAssignment(
        session_id=ts.id,
        teacher_id=teacher.id,
        target_player_id=target_player_id,
        target_room_id=target_room_id,
        level_id=level.id,
        difficulty_tier=tier,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return {
        "assignment_id": assignment.id,
        "session_code": ts.session_code,
        "level_code": level.level_code,
        "difficulty_tier": tier,
        "target_player_code": req.target_player_code,
        "target_room_code": req.target_room_code,
    }


@router.post("/api/teacher/sessions/{session_code}/difficulty")
def override_difficulty(
    session_code: str,
    req: DifficultyOverrideRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    ts = get_authorized_session(db, session_code, teacher)
    if req.difficulty_tier not in ("guided", "core", "challenge"):
        raise HTTPException(status_code=400, detail="難度層級必須為 guided、core 或 challenge")

    if req.target_player_code:
        player = db.query(Player).filter(Player.player_code == req.target_player_code.strip()).first()
        if not player:
            raise HTTPException(status_code=404, detail="找不到該學生代號")
        sm = (
            db.query(SessionMember)
            .filter(SessionMember.session_id == ts.id, SessionMember.player_id == player.id)
            .first()
        )
        if not sm:
            raise HTTPException(status_code=404, detail="該學生不在本場次中")
        sm.assigned_difficulty = req.difficulty_tier
        db.commit()
        return {"status": "updated", "target": player.player_code, "difficulty_tier": req.difficulty_tier}

    if req.target_room_code:
        room = db.query(Room).filter(Room.room_code == req.target_room_code.strip().upper()).first()
        if not room:
            raise HTTPException(status_code=404, detail="找不到該房間代碼")
        room.difficulty_tier = req.difficulty_tier
        db.commit()
        return {"status": "updated", "target": room.room_code, "difficulty_tier": req.difficulty_tier}

    raise HTTPException(status_code=400, detail="請提供 target_player_code 或 target_room_code")


@router.get("/api/teacher/sessions/{session_code}/export")
def export_anonymized_session_summary(
    session_code: str,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Exports anonymized classroom learning summary without any personal identifiable information (PII).
    """
    overview = get_session_overview(session_code, teacher, db)
    export_students = []
    for st in overview["students"]:
        export_students.append({
            "student_code": st["player_code"],
            "highest_chapter": st["highest_chapter"],
            "completed_levels_count": st["completed_count"],
            "completed_levels": st["completed_levels"],
            "concepts_seen": st["concepts_seen"],
            "self_corrections": st["self_corrections"],
            "descriptive_summary": st["descriptive_summary"],
        })

    return {
        "session_code": overview["session"]["session_code"],
        "display_name": overview["session"]["display_name"],
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "privacy_notice": "本匯出摘要僅包含匿名學員代號與概念學習歷程，不含真實姓名、電話或個資。",
        "total_students": len(export_students),
        "students": export_students,
        "coop_records": overview["coop_records"],
    }

