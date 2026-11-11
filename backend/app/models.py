from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Text,
    UniqueConstraint,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from .database import Base

def utcnow():
    return datetime.now(timezone.utc)


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    player_code = Column(String(32), unique=True, nullable=False, index=True)
    nickname = Column(String(64), nullable=False)
    character_skin = Column(String(32), default="nova_scout", nullable=False)
    head_accessory = Column(String(32), default="antenna_basic", nullable=False)
    color_theme = Column(String(32), default="cyan_core", nullable=False)
    base_decor = Column(String(32), default="holo_plant", nullable=False)
    title_badge = Column(String(64), default="實習修復員", nullable=False)
    experience = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    settings = relationship("PlayerSettings", back_populates="player", uselist=False, cascade="all, delete-orphan")
    progress = relationship("PlayerProgress", back_populates="player", cascade="all, delete-orphan")
    achievements = relationship("PlayerAchievement", back_populates="player", cascade="all, delete-orphan")
    room_memberships = relationship("RoomMember", back_populates="player", cascade="all, delete-orphan")
    session_memberships = relationship("SessionMember", back_populates="player", cascade="all, delete-orphan")
    learning_events = relationship("LearningEvent", back_populates="player", cascade="all, delete-orphan")


class PlayerSettings(Base):
    __tablename__ = "player_settings"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    sound_enabled = Column(Boolean, default=True, nullable=False)
    animation_level = Column(String(16), default="normal", nullable=False)  # normal | fast | reduced
    text_size = Column(String(16), default="medium", nullable=False)        # medium | large
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    player = relationship("Player", back_populates="settings")


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    auth_subject = Column(String(128), unique=True, nullable=False, index=True)
    display_name = Column(String(64), nullable=True)
    token_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    sessions = relationship("TeachingSession", back_populates="teacher", cascade="all, delete-orphan")
    assignments = relationship("TeacherAssignment", back_populates="teacher", cascade="all, delete-orphan")


class TeachingSession(Base):
    __tablename__ = "teaching_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_code = Column(String(16), unique=True, nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)
    display_name = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(24), default="active", nullable=False)  # active | closed | expired

    teacher = relationship("Teacher", back_populates="sessions")
    members = relationship("SessionMember", back_populates="session", cascade="all, delete-orphan")
    assignments = relationship("TeacherAssignment", back_populates="session", cascade="all, delete-orphan")


class SessionMember(Base):
    __tablename__ = "session_members"
    __table_args__ = (
        UniqueConstraint("session_id", "player_id", name="uq_session_member"),
    )

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("teaching_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True)
    joined_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    status = Column(String(24), default="active", nullable=False)
    assigned_difficulty = Column(String(16), nullable=True)  # guided | core | challenge | None

    session = relationship("TeachingSession", back_populates="members")
    player = relationship("Player", back_populates="session_memberships")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_code = Column(String(16), unique=True, nullable=False, index=True)
    host_player_id = Column(Integer, ForeignKey("players.id", ondelete="SET NULL"), nullable=True, index=True)
    editor_player_id = Column(Integer, ForeignKey("players.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(Integer, ForeignKey("teaching_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(24), default="waiting", nullable=False)  # waiting | playing | completed | closed
    current_level = Column(String(32), default="ch1_lv1", nullable=False)
    difficulty_tier = Column(String(16), default="guided", nullable=False)  # guided | core | challenge
    turn_index = Column(Integer, default=0, nullable=False)
    editor_locked = Column(Boolean, default=False, nullable=False)
    workspace_state = Column(JSON, default=dict, nullable=False)
    turn_history = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    members = relationship("RoomMember", back_populates="room", cascade="all, delete-orphan")
    mission_records = relationship("MissionRecord", back_populates="room", cascade="all, delete-orphan")


class RoomMember(Base):
    __tablename__ = "room_members"
    __table_args__ = (
        UniqueConstraint("room_id", "player_id", name="uq_room_player"),
    )

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(32), default="all_rounder", nullable=False)
    is_ready = Column(Boolean, default=True, nullable=False)
    is_observer = Column(Boolean, default=False, nullable=False)
    is_online = Column(Boolean, default=True, nullable=False)
    joined_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    room = relationship("Room", back_populates="members")
    player = relationship("Player", back_populates="room_memberships")


class Level(Base):
    __tablename__ = "levels"

    id = Column(Integer, primary_key=True, index=True)
    level_code = Column(String(32), unique=True, nullable=False, index=True)
    chapter_id = Column(Integer, nullable=False, index=True)
    chapter_name = Column(String(64), nullable=False)
    level_order = Column(Integer, nullable=False)
    level_name = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(16), default="core", nullable=False)
    learning_objective = Column(Text, nullable=False)
    concept_code = Column(String(32), nullable=False, index=True)
    editor_mode = Column(String(24), default="blockly", nullable=False)  # cards | hybrid | blockly
    level_data = Column(JSON, nullable=False)

    variants = relationship("LevelVariant", back_populates="level", cascade="all, delete-orphan")


class LevelVariant(Base):
    __tablename__ = "level_variants"
    __table_args__ = (
        UniqueConstraint("level_id", "difficulty_tier", name="uq_level_variant_tier"),
    )

    id = Column(Integer, primary_key=True, index=True)
    level_id = Column(Integer, ForeignKey("levels.id", ondelete="CASCADE"), nullable=False, index=True)
    difficulty_tier = Column(String(16), nullable=False)  # guided | core | challenge
    level_data = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    level = relationship("Level", back_populates="variants")


class PlayerProgress(Base):
    __tablename__ = "player_progress"
    __table_args__ = (
        UniqueConstraint("player_id", "level_id", "difficulty_tier", name="uq_player_level_tier"),
    )

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True)
    level_id = Column(Integer, ForeignKey("levels.id", ondelete="CASCADE"), nullable=False, index=True)
    difficulty_tier = Column(String(16), default="guided", nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    stars = Column(Integer, default=0, nullable=False)
    best_result = Column(JSON, default=dict, nullable=False)
    saved_workspace = Column(JSON, default=dict, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    player = relationship("Player", back_populates="progress")
    level = relationship("Level")


class MissionRecord(Base):
    __tablename__ = "mission_records"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="SET NULL"), nullable=True, index=True)
    level_id = Column(Integer, ForeignKey("levels.id", ondelete="CASCADE"), nullable=False, index=True)
    difficulty_tier = Column(String(16), default="guided", nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    attempts = Column(Integer, default=1, nullable=False)
    hints_used = Column(Integer, default=0, nullable=False)
    completion_time = Column(Integer, default=0, nullable=False)  # seconds (auxiliary info only, not primary score)
    role_distribution = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    room = relationship("Room", back_populates="mission_records")


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    achievement_code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(32), default="learning", nullable=False)
    reward_type = Column(String(32), default="badge", nullable=False)  # skin | accessory | decor | title | badge
    reward_value = Column(String(64), default="", nullable=False)
    xp_reward = Column(Integer, default=50, nullable=False)


class PlayerAchievement(Base):
    __tablename__ = "player_achievements"
    __table_args__ = (
        UniqueConstraint("player_id", "achievement_id", name="uq_player_achievement"),
    )

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False, index=True)
    unlocked_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    player = relationship("Player", back_populates="achievements")
    achievement = relationship("Achievement")


class LearningEvent(Base):
    __tablename__ = "learning_events"
    __table_args__ = (
        Index("ix_learning_events_player_concept", "player_id", "concept_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True, index=True)
    session_id = Column(Integer, ForeignKey("teaching_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    level_id = Column(Integer, ForeignKey("levels.id", ondelete="SET NULL"), nullable=True, index=True)
    difficulty_tier = Column(String(16), default="guided", nullable=False)
    concept_code = Column(String(32), nullable=False, index=True)
    event_type = Column(String(32), nullable=False, index=True)  # concept_seen | program_run | error_occurred | self_corrected | hint_used | level_completed | reflection_answered
    event_data = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    player = relationship("Player", back_populates="learning_events")


class TeacherAssignment(Base):
    __tablename__ = "teacher_assignments"
    __table_args__ = (
        CheckConstraint(
            "(target_player_id IS NOT NULL AND target_room_id IS NULL) OR (target_player_id IS NULL AND target_room_id IS NOT NULL)",
            name="ck_assignment_target_xor",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("teaching_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)
    target_player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=True, index=True)
    target_room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=True, index=True)
    level_id = Column(Integer, ForeignKey("levels.id", ondelete="CASCADE"), nullable=False, index=True)
    difficulty_tier = Column(String(16), default="guided", nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    session = relationship("TeachingSession", back_populates="assignments")
    teacher = relationship("Teacher", back_populates="assignments")
    level = relationship("Level")

