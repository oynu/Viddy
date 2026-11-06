import os
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from backend.database import crud
from backend.database.models import JobModel, VideoModel

class RecoveryManager:
    """
    Detects in-flight or interrupted jobs and videos from previous application runs
    and recovers the system into a healthy state upon startup, purging stale temp assets.
    """
    def __init__(self, db_path: Optional[str] = None, storage_dir: Optional[str] = None):
        self.db_path = db_path
        self.storage_dir = Path(storage_dir) if storage_dir else None

    def recover_interrupted_jobs(self, session: Session) -> int:
        """
        Marks any abandoned 'in_progress' jobs and videos as 'recovered'
        and cleans up temporary folders older than 1 hour.
        """
        interrupted_jobs = session.query(JobModel).filter(JobModel.status == "in_progress").all()
        interrupted_videos = session.query(VideoModel).filter(VideoModel.status == "in_progress").all()
        
        count = len(interrupted_jobs) + len(interrupted_videos)
        
        for job in interrupted_jobs:
            job.status = "recovered"
            job.current_action = "Recovered after application restart"
            job.updated_at = datetime.now(timezone.utc)
            crud.add_log(session, f"Job #{job.id} ({job.stage}) recovered after restart.", stage="RECOVERY", level="WARNING")
            
        for video in interrupted_videos:
            video.status = "recovered"
            video.error_message = "Production interrupted by application shutdown"
            crud.add_log(session, f"Video #{video.id} ('{video.title}') recovered after restart.", stage="RECOVERY", level="WARNING")

        session.commit()
        
        # Cleanup stale temp production folders
        self._cleanup_stale_temp_dirs()
        
        return count

    def _cleanup_stale_temp_dirs(self):
        """Removes temporary production directories older than 1 hour."""
        if not self.storage_dir or not self.storage_dir.exists():
            return
            
        now = datetime.now(timezone.utc)
        try:
            for item in self.storage_dir.iterdir():
                if item.is_dir() and item.name.startswith("prod_"):
                    # Check age of folder
                    mtime = datetime.fromtimestamp(item.stat().st_mtime, tz=timezone.utc)
                    if now - mtime > timedelta(hours=1):
                        shutil.rmtree(item, ignore_errors=True)
        except Exception:
            pass
