from typing import Any, Optional
from pydantic import BaseModel, Field


class PlayerCreateRequest(BaseModel):
    nickname: Optional[str] = None
    player_code: Optional[str] = None
    character_skin: str = "nova_scout"


class PlayerUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    character_skin: Optional[str] = None
    head_accessory: Optional[str] = None
    color_theme: Optional[str] = None
    base_decor: Optional[str] = None
    title_badge: Optional[str] = None


class PlayerSettingsUpdate(BaseModel):
    sound_enabled: Optional[bool] = None
    animation_level: Optional[str] = None
    text_size: Optional[str] = None


class WorkspaceSaveRequest(BaseModel):
    player_code: str
    level_code: str
    difficulty_tier: str = "guided"
    workspace_data: dict[str, Any]


class ProgramSubmitRequest(BaseModel):
    player_code: str
    room_code: Optional[str] = None
    difficulty_tier: str = "guided"
    program_ast: list[dict[str, Any]] = Field(default_factory=list)
    workspace_data: dict[str, Any] = Field(default_factory=dict)
    hints_used: int = 0
    attempts: int = 1
    completion_time: int = 0
    reflection_answer: Optional[str] = None


class LearningEventCreateRequest(BaseModel):
    player_code: str
    room_code: Optional[str] = None
    level_code: Optional[str] = None
    difficulty_tier: str = "guided"
    concept_code: str
    event_type: str
    event_data: dict[str, Any] = Field(default_factory=dict)


class RoomCreateRequest(BaseModel):
    player_code: str
    level_code: str = "ch1_lv1"
    difficulty_tier: str = "guided"
    session_code: Optional[str] = None


class RoomJoinRequest(BaseModel):
    player_code: str
    room_code: str


class RoomLeaveRequest(BaseModel):
    player_code: str
    room_code: str


class RoomActionRequest(BaseModel):
    player_code: str
    level_code: Optional[str] = None
    difficulty_tier: Optional[str] = None
    workspace_state: Optional[dict[str, Any]] = None


class TeacherLoginRequest(BaseModel):
    passkey: str
    display_name: str = "資訊科技教師"


class SessionCreateRequest(BaseModel):
    display_name: str
    expires_hours: int = 24


class SessionJoinRequest(BaseModel):
    player_code: str
    session_code: str


class AssignmentCreateRequest(BaseModel):
    target_player_code: Optional[str] = None
    target_room_code: Optional[str] = None
    level_code: str
    difficulty_tier: str = "core"


class DifficultyOverrideRequest(BaseModel):
    target_player_code: Optional[str] = None
    target_room_code: Optional[str] = None
    difficulty_tier: str

