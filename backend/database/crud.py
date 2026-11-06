from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.database.models import (
    SettingModel, VideoModel, JobModel, IdeaHistoryModel, PlatformAccountModel, LogEntryModel
)

def utcnow():
    return datetime.now(timezone.utc)

# Settings
def get_settings(session: Session) -> SettingModel:
    setting = session.query(SettingModel).filter(SettingModel.id == 1).first()
    if not setting:
        setting = SettingModel(id=1)
        session.add(setting)
        session.commit()
        session.refresh(setting)
    return setting

def update_settings(session: Session, **kwargs) -> SettingModel:
    setting = get_settings(session)
    for key, value in kwargs.items():
        if hasattr(setting, key) and value is not None:
            setattr(setting, key, value)
    setting.updated_at = utcnow()
    session.commit()
    session.refresh(setting)
    return setting

# Videos
def create_video(
    session: Session,
    title: str,
    topic: str,
    script: str,
    duration: float = 0.0,
    category: str = "science",
    hook: Optional[str] = None,
    status: str = "pending"
) -> VideoModel:
    video = VideoModel(
        title=title,
        topic=topic,
        category=category,
        script=script,
        hook=hook,
        duration=duration,
        status=status,
        created_at=utcnow()
    )
    session.add(video)
    session.commit()
    session.refresh(video)
    return video

def get_video_by_id(session: Session, video_id: int) -> Optional[VideoModel]:
    return session.query(VideoModel).filter(VideoModel.id == video_id).first()

def get_all_videos(session: Session, limit: int = 50) -> List[VideoModel]:
    return session.query(VideoModel).order_by(VideoModel.id.desc()).limit(limit).all()

def update_video(session: Session, video_id: int, **kwargs) -> Optional[VideoModel]:
    video = get_video_by_id(session, video_id)
    if not video:
        return None
    for key, value in kwargs.items():
        if hasattr(video, key) and value is not None:
            setattr(video, key, value)
    if kwargs.get("status") == "completed" and not video.completed_at:
        video.completed_at = utcnow()
    session.commit()
    session.refresh(video)
    return video

# Jobs
def create_job(session: Session, stage: str, video_id: Optional[int] = None) -> JobModel:
    job = JobModel(
        stage=stage,
        video_id=video_id,
        status="in_progress",
        progress=0.0,
        current_action=f"Starting {stage} phase",
        created_at=utcnow()
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job

def get_job_by_id(session: Session, job_id: int) -> Optional[JobModel]:
    return session.query(JobModel).filter(JobModel.id == job_id).first()

def get_active_job(session: Session) -> Optional[JobModel]:
    return session.query(JobModel).filter(JobModel.status == "in_progress").order_by(JobModel.id.desc()).first()

def update_job(session: Session, job_id: int, **kwargs) -> Optional[JobModel]:
    job = get_job_by_id(session, job_id)
    if not job:
        return None
    for key, value in kwargs.items():
        if hasattr(job, key) and value is not None:
            setattr(job, key, value)
    job.updated_at = utcnow()
    session.commit()
    session.refresh(job)
    return job

# Idea History
def record_idea_history(session: Session, title: str, category: str, hook_angle: str = "", keywords: str = "", score: float = 8.0) -> IdeaHistoryModel:
    idea = IdeaHistoryModel(
        title=title,
        category=category,
        hook_angle=hook_angle,
        keywords=keywords,
        curiosity_score=score,
        created_at=utcnow()
    )
    session.add(idea)
    session.commit()
    session.refresh(idea)
    return idea

def is_title_in_history(session: Session, title: str) -> bool:
    title_norm = title.strip().lower()
    match = session.query(IdeaHistoryModel).filter(IdeaHistoryModel.title.ilike(f"%{title_norm}%")).first()
    return match is not None

def get_recent_ideas(session: Session, limit: int = 100) -> List[IdeaHistoryModel]:
    return session.query(IdeaHistoryModel).order_by(IdeaHistoryModel.id.desc()).limit(limit).all()

# Accounts
def get_platform_account(session: Session, platform: str) -> Optional[PlatformAccountModel]:
    return session.query(PlatformAccountModel).filter(PlatformAccountModel.platform == platform).first()

def upsert_platform_account(session: Session, platform: str, **kwargs) -> PlatformAccountModel:
    acc = get_platform_account(session, platform)
    if not acc:
        acc = PlatformAccountModel(platform=platform)
        session.add(acc)
    for key, value in kwargs.items():
        if hasattr(acc, key):
            setattr(acc, key, value)
    acc.updated_at = utcnow()
    session.commit()
    session.refresh(acc)
    return acc

# Logs
def add_log(session: Session, message: str, stage: str = "GENERAL", level: str = "INFO") -> LogEntryModel:
    log_entry = LogEntryModel(
        message=message,
        stage=stage,
        level=level,
        created_at=utcnow()
    )
    session.add(log_entry)
    session.commit()
    session.refresh(log_entry)
    return log_entry

def get_recent_logs(session: Session, limit: int = 100) -> List[LogEntryModel]:
    return session.query(LogEntryModel).order_by(LogEntryModel.id.desc()).limit(limit).all()
