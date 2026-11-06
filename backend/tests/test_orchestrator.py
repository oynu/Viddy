import pytest
import asyncio
from backend.orchestrator.worker import AutonomousWorker
from backend.database.session import init_db, get_db
from backend.database import crud

@pytest.mark.asyncio
async def test_worker_lifecycle_controls(tmp_path):
    db_file = tmp_path / "test_orch.db"
    init_db(str(db_file))
    
    worker = AutonomousWorker(db_path=str(db_file), simulated_media=True, cycle_delay_seconds=0.1)
    assert worker.state == "STOPPED"
    
    # Start the continuous agent
    await worker.start()
    assert worker.state == "RUNNING"
    
    # Pause the continuous agent
    await worker.pause()
    assert worker.state == "PAUSED"
    
    # Resume the continuous agent
    await worker.resume()
    assert worker.state == "RUNNING"
    
    # Stop the continuous agent
    await worker.stop()
    assert worker.state == "STOPPED"

@pytest.mark.asyncio
async def test_worker_single_cycle_execution(tmp_path):
    db_file = tmp_path / "test_cycle.db"
    init_db(str(db_file))
    
    worker = AutonomousWorker(
        db_path=str(db_file),
        storage_dir=str(tmp_path / "media"),
        simulated_media=True,
        cycle_delay_seconds=0.1
    )
    
    # Execute a single production cycle
    video_id = await worker.run_single_production_cycle()
    assert video_id is not None
    
    with get_db(str(db_file)) as session:
        video = crud.get_video_by_id(session, video_id)
        assert video is not None
        assert video.status in ["completed", "published"]
        assert len(video.title) > 5
        assert video.qc_passed is True
