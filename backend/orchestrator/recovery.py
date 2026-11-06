from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from backend.database import crud
from backend.database.models import JobModel

class RecoveryManager:
    """
    Detects in-flight or interrupted jobs from previous application runs
    and recovers the system into a healthy state upon startup.
    """
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def recover_interrupted_jobs(self, session: Session) -> int:
        """
        Marks any abandoned 'in_progress' jobs as 'recovered' so the autonomous
        worker can resume without stale lockups.
        """
        interrupted = session.query(JobModel).filter(JobModel.status == "in_progress").all()
        count = len(interrupted)
        for job in interrupted:
            job.status = "recovered"
            job.current_action = "Recovered after application restart"
            job.updated_at = datetime.now(timezone.utc)
            crud.add_log(session, f"Job #{job.id} ({job.stage}) recovered after restart.", stage="RECOVERY", level="WARNING")
            
        session.commit()
        return count
