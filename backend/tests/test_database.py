import pytest
from backend.database.session import init_db, get_db
from backend.database import crud
from backend.database.models import SettingModel, VideoModel, JobModel

def test_database_initialization_and_crud(tmp_path):
    db_file = tmp_path / "test_viddy.db"
    init_db(str(db_file))
    
    with get_db(str(db_file)) as session:
        # Check default settings are created
        settings = crud.get_settings(session)
        assert settings.running_mode == "continuous"
        assert settings.publish_destination in ["local", "both", "youtube", "tiktok"]
        
        # Test creating and fetching video
        video = crud.create_video(
            session,
            title="What if the Moon vanished?",
            topic="Astrophysics",
            script="Imagine looking up at the night sky...",
            duration=35.0,
            status="completed"
        )
        assert video.id is not None
        fetched = crud.get_video_by_id(session, video.id)
        assert fetched.title == "What if the Moon vanished?"
        assert fetched.duration == 35.0
        
        # Test updating video
        updated = crud.update_video(session, video.id, youtube_url="https://youtube.com/shorts/xyz123")
        assert updated.youtube_url == "https://youtube.com/shorts/xyz123"
        
        # Test job creation and status transition
        job = crud.create_job(session, stage="DISCOVER", video_id=video.id)
        assert job.id is not None
        assert job.status == "in_progress"
        
        crud.update_job(session, job.id, status="completed", progress=100.0)
        completed_job = crud.get_job_by_id(session, job.id)
        assert completed_job.status == "completed"
        assert completed_job.progress == 100.0
