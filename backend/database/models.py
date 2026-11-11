from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def get_utc_now():
    return datetime.now(timezone.utc)

class SettingModel(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, default=1)
    running_mode = Column(String(50), default="stopped")  # stopped, continuous, limited, paused
    publish_destination = Column(String(50), default="tiktok")  # tiktok, youtube, both, local
    max_daily_videos = Column(Integer, default=24)
    daily_videos_produced = Column(Integer, default=0)
    last_reset_date = Column(String(20), default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    cycle_delay_seconds = Column(Integer, default=10)
    target_duration_seconds = Column(Integer, default=45)
    default_voice = Column(String(100), default="en-US-ChristopherNeural")
    ai_provider = Column(String(50), default="heuristic")  # heuristic, gemini, openai
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

class VideoModel(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    topic = Column(String(100), nullable=False)
    category = Column(String(50), default="science")
    script = Column(Text, nullable=False)
    hook = Column(Text, nullable=True)
    duration = Column(Float, default=0.0)
    status = Column(String(50), default="pending")  # pending, rendering, qc_passed, published, failed
    
    video_path = Column(String(500), nullable=True)
    audio_path = Column(String(500), nullable=True)
    thumbnail_path = Column(String(500), nullable=True)
    subtitle_path = Column(String(500), nullable=True)
    
    published_destinations = Column(String(100), default="none")
    youtube_url = Column(String(500), nullable=True)
    tiktok_url = Column(String(500), nullable=True)
    
    tiktok_commentary = Column(Text, nullable=True)
    tiktok_hashtags = Column(Text, nullable=True)
    youtube_tags = Column(Text, nullable=True)
    
    qc_passed = Column(Boolean, default=False)
    qc_details = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=get_utc_now)
    completed_at = Column(DateTime, nullable=True)
    
    jobs = relationship("JobModel", back_populates="video", cascade="all, delete-orphan")

class JobModel(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=True)
    stage = Column(String(50), nullable=False)  # DISCOVER, RESEARCH, SCRIPT, SCENE_PLAN, RENDER_3D, AUDIO, QC, PUBLISH
    status = Column(String(50), default="in_progress")  # in_progress, completed, failed, paused
    progress = Column(Float, default=0.0)  # 0.0 - 100.0
    current_action = Column(String(255), default="Initializing")
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    video = relationship("VideoModel", back_populates="jobs")

class IdeaHistoryModel(Base):
    __tablename__ = "idea_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), unique=True, nullable=False)
    category = Column(String(50), nullable=False)
    hook_angle = Column(String(255), nullable=True)
    keywords = Column(String(500), nullable=True)
    curiosity_score = Column(Float, default=8.0)
    created_at = Column(DateTime, default=get_utc_now)

class PlatformAccountModel(Base):
    __tablename__ = "platform_accounts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), unique=True, nullable=False)  # youtube, tiktok
    account_name = Column(String(100), nullable=True)
    channel_id = Column(String(100), nullable=True)
    is_connected = Column(Boolean, default=False)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    credentials_json = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

class LogEntryModel(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(20), default="INFO")  # INFO, WARNING, ERROR, SUCCESS
    stage = Column(String(50), default="GENERAL")
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=get_utc_now)
