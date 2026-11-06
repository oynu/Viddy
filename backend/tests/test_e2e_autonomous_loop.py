import pytest
import asyncio
from backend.orchestrator.worker import AutonomousWorker
from backend.database.session import init_db, get_db
from backend.database import crud

@pytest.mark.asyncio
async def test_autonomous_consecutive_productions(tmp_path):
    db_file = tmp_path / "test_e2e.db"
    init_db(str(db_file))
    
    # Configure worker for continuous operation with fast cycle delay in test mode
    worker = AutonomousWorker(
        db_path=str(db_file),
        storage_dir=str(tmp_path / "media"),
        simulated_media=True,
        cycle_delay_seconds=0.05
    )
    
    # Start the autonomous background loop
    await worker.start()
    assert worker.state == "RUNNING"
    
    # Wait for the continuous loop to autonomously produce at least 2 consecutive videos
    max_wait_seconds = 10.0
    elapsed = 0.0
    produced_count = 0
    
    while elapsed < max_wait_seconds:
        await asyncio.sleep(0.2)
        elapsed += 0.2
        with get_db(str(db_file)) as session:
            completed_videos = crud.get_all_videos(session)
            if len(completed_videos) >= 2:
                produced_count = len(completed_videos)
                break
                
    # Stop the worker safely
    await worker.stop()
    assert worker.state == "STOPPED"
    
    # Assertions on autonomous execution
    assert produced_count >= 2, f"Expected at least 2 autonomous productions, got {produced_count}"
    
    with get_db(str(db_file)) as session:
        videos = crud.get_all_videos(session)
        assert len(videos) >= 2
        # Verify continuous novelty: titles must be completely distinct
        assert videos[0].title != videos[1].title
        # Verify both videos successfully completed and passed QC
        for v in videos[:2]:
            assert v.status == "completed"
            assert v.qc_passed is True
            assert v.duration > 0
            assert len(v.script) > 20
            assert v.published_destinations in ["local", "youtube", "tiktok", "both"]
