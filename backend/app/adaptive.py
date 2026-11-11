from typing import Any
from sqlalchemy.orm import Session
from .models import LearningEvent, PlayerProgress, Level, TeacherAssignment, SessionMember

CONCEPT_NAMES = {
    "sequence": "指令與執行順序",
    "loops": "迴圈與重複執行",
    "conditions": "條件判斷 (if/else)",
    "variables": "變數與數值管理",
    "logic": "邏輯運算 (AND/OR/NOT)",
    "functions": "自訂函式與模組化",
    "integration": "綜合問題拆解與除錯",
}

ERROR_DESCRIPTIONS = {
    "obstacle_collision": "前方障礙物碰撞（方向或步數估算誤差）",
    "out_of_bounds": "超出基地平台邊界（步數過多）",
    "door_locked": "閘門開啟條件未滿足即嘗試通過",
    "not_at_goal": "路徑規劃尚未抵達終點",
    "missing_energy": "經過能源晶片但未執行撿取或數量不足",
    "loop_limit_exceeded": "迴圈次數設定過大或終止條件未達成",
}


def compute_player_learning_summary(db: Session, player_id: int, session_id: int | None = None) -> dict[str, Any]:
    """
    Computes evidence-based learning summary and conservative difficulty recommendations
    strictly from recorded LearningEvent and PlayerProgress rows.
    """
    events = (
        db.query(LearningEvent)
        .filter(LearningEvent.player_id == player_id)
        .order_by(LearningEvent.created_at.asc())
        .all()
    )
    progress_rows = (
        db.query(PlayerProgress)
        .filter(PlayerProgress.player_id == player_id)
        .all()
    )
    levels_by_id = {lv.id: lv for lv in db.query(Level).all()}

    concepts_seen = set()
    concepts_completed_guided = set()
    concepts_completed_core_count: dict[str, int] = {}
    concepts_completed_challenge = set()
    error_counts: dict[str, int] = {}
    self_corrections = 0
    hints_used_total = 0
    total_runs = 0

    recent_errors_in_current_level = 0
    for ev in events:
        c_code = ev.concept_code or "sequence"
        concepts_seen.add(c_code)
        if ev.event_type == "program_run":
            total_runs += 1
        elif ev.event_type == "error_occurred":
            err_t = ev.event_data.get("error_type", "unknown")
            error_counts[err_t] = error_counts.get(err_t, 0) + 1
            recent_errors_in_current_level += 1
        elif ev.event_type == "self_corrected":
            self_corrections += 1
            recent_errors_in_current_level = 0
        elif ev.event_type == "hint_used":
            hints_used_total += 1
        elif ev.event_type == "level_completed":
            recent_errors_in_current_level = 0
            tier = ev.difficulty_tier or "guided"
            hints_in_run = int(ev.event_data.get("hints_used", 0))
            if tier == "guided":
                concepts_completed_guided.add(c_code)
            elif tier == "core":
                if hints_in_run <= 1:
                    concepts_completed_core_count[c_code] = concepts_completed_core_count.get(c_code, 0) + 1
                else:
                    concepts_completed_guided.add(c_code)
            elif tier == "challenge":
                concepts_completed_challenge.add(c_code)

    for pr in progress_rows:
        if pr.completed:
            lv = levels_by_id.get(pr.level_id)
            c_code = lv.concept_code if lv else "sequence"
            concepts_seen.add(c_code)
            if pr.difficulty_tier == "guided":
                concepts_completed_guided.add(c_code)
            elif pr.difficulty_tier == "core":
                concepts_completed_core_count[c_code] = max(concepts_completed_core_count.get(c_code, 0), 1)
            elif pr.difficulty_tier == "challenge":
                concepts_completed_challenge.add(c_code)

    # Generate conservative per-concept difficulty recommendations
    recommendations: dict[str, dict[str, str]] = {}
    for c_code, c_name in CONCEPT_NAMES.items():
        if c_code in concepts_completed_challenge or concepts_completed_core_count.get(c_code, 0) >= 2:
            rec_tier = "challenge"
            reason = f"已在多個不同任務情境中獨立運用「{c_name}」，推薦嘗試挑戰層級比較不同解法。"
        elif c_code in concepts_completed_guided or concepts_completed_core_count.get(c_code, 0) >= 1:
            rec_tier = "core"
            reason = f"已理解「{c_name}」的基礎操作，推薦進入標準層級自行規劃程式。"
        else:
            rec_tier = "guided"
            reason = f"初次或正在建立「{c_name}」概念，建議從基礎引導開始觀察機器人行為。"

        recommendations[c_code] = {
            "recommended_tier": rec_tier,
            "reason": reason,
        }

    # Check if teacher manually assigned a difficulty or task
    teacher_override = None
    if session_id:
        sm = (
            db.query(SessionMember)
            .filter(SessionMember.session_id == session_id, SessionMember.player_id == player_id)
            .first()
        )
        if sm and sm.assigned_difficulty:
            teacher_override = sm.assigned_difficulty

    assignment = (
        db.query(TeacherAssignment)
        .filter(TeacherAssignment.target_player_id == player_id)
        .order_by(TeacherAssignment.created_at.desc())
        .first()
    )
    if assignment and not teacher_override:
        teacher_override = assignment.difficulty_tier

    # Generate human-readable teacher observations based strictly on recorded evidence
    descriptive_notes: list[str] = []
    if "sequence" in concepts_completed_guided or concepts_completed_core_count.get("sequence", 0) > 0:
        descriptive_notes.append("已能正確排列移動與轉向指令順序完成基本路徑規劃。")
    if "loops" in concepts_completed_guided or concepts_completed_core_count.get("loops", 0) > 0:
        descriptive_notes.append("已能使用固定次數迴圈完成直線與重複移動任務。")
    if "conditions" in concepts_completed_guided or concepts_completed_core_count.get("conditions", 0) > 0:
        descriptive_notes.append("已能在迷宮或門鎖情境中使用條件判斷 (if/else) 選擇行動。")
    if "variables" in concepts_completed_guided or concepts_completed_core_count.get("variables", 0) > 0:
        descriptive_notes.append("已能透過變數追蹤能源數量並使用比較判斷開啟閘門。")
    if "logic" in concepts_completed_guided or concepts_completed_core_count.get("logic", 0) > 0:
        descriptive_notes.append("已能使用 AND / OR / NOT 組合多重控制條件。")
    if "functions" in concepts_completed_guided or concepts_completed_core_count.get("functions", 0) > 0:
        descriptive_notes.append("已能建立自訂函式並重複呼叫以簡化大型任務。")

    if self_corrections > 0:
        descriptive_notes.append(f"曾 {self_corrections} 次在觀察錯誤提示後自行修正程式並成功通關。")

    if error_counts:
        top_err = max(error_counts.items(), key=lambda x: x[1])
        err_label = ERROR_DESCRIPTIONS.get(top_err[0], top_err[0])
        descriptive_notes.append(f"常見需留意的錯誤類型為：{err_label}（累計 {top_err[1]} 次）。")

    if not descriptive_notes:
        descriptive_notes.append("剛開始探索 NOVA 基地，尚在熟悉基本指令操作。")

    return {
        "concepts_seen": sorted(list(concepts_seen)),
        "concepts_mastered_core": sorted([k for k, v in concepts_completed_core_count.items() if v >= 1]),
        "concepts_challenge_completed": sorted(list(concepts_completed_challenge)),
        "total_runs": total_runs,
        "self_corrections": self_corrections,
        "hints_used_total": hints_used_total,
        "error_breakdown": error_counts,
        "recommendations": recommendations,
        "teacher_override_difficulty": teacher_override,
        "descriptive_summary": descriptive_notes,
    }

