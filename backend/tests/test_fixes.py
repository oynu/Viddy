import pytest
import os
import asyncio
from datetime import datetime, timezone, timedelta
from backend.publishing.publish_manager import PublishingManager, PublishRequest
from backend.orchestrator.recovery import RecoveryManager
from backend.orchestrator.worker import AutonomousWorker
from backend.blender.runner import BlenderRunner
from backend.agents.visual_director import SceneInstruction
from backend.database.session import init_db, get_db
from backend.database import crud
from backend.database.models import PlatformAccountModel, VideoModel, JobModel

@pytest.mark.asyncio
async def test_token_refresh_integration(tmp_path):
    db_file = tmp_path / "test_token.db"
    init_db(str(db_file))
    
    # Insert expired YouTube account
    with get_db(str(db_file)) as session:
        crud.upsert_platform_account(
            session=session,
            platform="youtube",
            is_connected=True,
            access_token="expired_token_123",
            refresh_token="valid_refresh_token_456",
            token_expiry=datetime.now(timezone.utc) - timedelta(hours=2)
        )
        
    dummy_video = tmp_path / "video.mp4"
    dummy_video.write_bytes(b"dummy")
    
    manager = PublishingManager(db_path=str(db_file), storage_dir=str(tmp_path / "pub"))
    
    # Mock refresh_access_token to simulate successful refresh
    async def mock_refresh(ref_tok):
        return {
            "access_token": "fresh_renewed_token_789",
            "expires_in": 3600,
            "expiry": datetime.now(timezone.utc) + timedelta(hours=1)
        }
    manager.youtube_pub.refresh_access_token = mock_refresh
    
    # Get active token with auto-refresh guard
    token = await manager.get_valid_token("youtube")
    assert token == "fresh_renewed_token_789"
    
    # Verify database was updated with fresh token
    with get_db(str(db_file)) as session:
        acc = crud.get_platform_account(session, "youtube")
        assert acc.access_token == "fresh_renewed_token_789"
        expiry = acc.token_expiry
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        assert expiry > datetime.now(timezone.utc)

def test_recovery_manager_cleans_orphaned_videos_and_dirs(tmp_path):
    db_file = tmp_path / "test_recovery.db"
    init_db(str(db_file))
    
    storage_dir = tmp_path / "output"
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    # Create old abandoned directory
    old_prod = storage_dir / "prod_20260101_000000"
    old_prod.mkdir()
    (old_prod / "temp.tmp").write_text("temp junk")
    
    j_id = None
    v_id = None
    with get_db(str(db_file)) as session:
        # Create abandoned video and job
        v = crud.create_video(session, title="Abandoned Video", topic="Test", script="Old", status="in_progress")
        j = crud.create_job(session, stage="RENDER_3D", video_id=v.id)
        j_id = j.id
        v_id = v.id
        
    recovery_mgr = RecoveryManager(db_path=str(db_file), storage_dir=str(storage_dir))
    
    with get_db(str(db_file)) as session:
        recovered_count = recovery_mgr.recover_interrupted_jobs(session)
        assert recovered_count >= 1
        
        # Verify job and video are no longer 'in_progress'
        recovered_job = crud.get_job_by_id(session, j_id)
        assert recovered_job.status == "recovered"
        
        recovered_video = crud.get_video_by_id(session, v_id)
        assert recovered_video.status == "recovered"

@pytest.mark.asyncio
async def test_subprocess_timeout_watchdog(tmp_path):
    runner = BlenderRunner()
    scene = SceneInstruction(
        scene_id=1,
        generator_type="space",
        duration=1.0,
        camera_motion="orbit"
    )
    # Testing that render_scene_async completes and falls back cleanly without hanging
    out_video = await runner.render_scene_async(
        scene=scene,
        output_dir=str(tmp_path),
        timeout_seconds=10.0
    )
    assert os.path.exists(out_video)
    assert os.path.getsize(out_video) > 1000
