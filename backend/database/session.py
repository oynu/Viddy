import os
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from backend.config import settings
from backend.database.models import Base, SettingModel

_engine = None
_SessionFactory = None

def get_engine(db_path: str = None):
    global _engine, _SessionFactory
    if db_path:
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        return engine
    if _engine is None:
        _engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
        _SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine

def init_db(db_path: str = None):
    engine = get_engine(db_path)
    Base.metadata.create_all(bind=engine)
    
    # Lightweight migration check for newly added columns in SQLite
    with engine.connect() as conn:
        try:
            res = conn.execute(text("PRAGMA table_info(videos)")).fetchall()
            existing_cols = {row[1] for row in res}
            if existing_cols:
                if "tiktok_commentary" not in existing_cols:
                    conn.execute(text("ALTER TABLE videos ADD COLUMN tiktok_commentary TEXT"))
                if "tiktok_hashtags" not in existing_cols:
                    conn.execute(text("ALTER TABLE videos ADD COLUMN tiktok_hashtags TEXT"))
                if "youtube_tags" not in existing_cols:
                    conn.execute(text("ALTER TABLE videos ADD COLUMN youtube_tags TEXT"))
                conn.commit()
        except Exception:
            pass

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with SessionLocal() as session:
        # Ensure default setting exists
        setting = session.query(SettingModel).filter(SettingModel.id == 1).first()
        if not setting:
            setting = SettingModel(
                id=1,
                running_mode=settings.default_running_mode,
                publish_destination=settings.default_destination,
                max_daily_videos=settings.max_daily_videos,
                cycle_delay_seconds=settings.min_cycle_delay_seconds
            )
            session.add(setting)
            session.commit()

@contextmanager
def get_db(db_path: str = None) -> Generator[Session, None, None]:
    engine = get_engine(db_path)
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        # Ensure default settings exist
        st = session.query(SettingModel).filter(SettingModel.id == 1).first()
        if not st:
            st = SettingModel(
                id=1,
                running_mode=settings.default_running_mode,
                publish_destination=settings.default_destination,
                max_daily_videos=settings.max_daily_videos,
                cycle_delay_seconds=settings.min_cycle_delay_seconds
            )
            session.add(st)
            session.commit()
        yield session
    finally:
        session.close()
