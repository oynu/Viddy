import os
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
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
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
