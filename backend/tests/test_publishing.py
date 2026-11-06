import pytest
import os
from backend.publishing.publish_manager import PublishingManager, PublishRequest, PublishResult
from backend.database.session import init_db, get_db

@pytest.mark.asyncio
async def test_local_publishing(tmp_path):
    db_file = tmp_path / "test_pub.db"
    init_db(str(db_file))
    
    # Create dummy video file
    dummy_video = tmp_path / "test_video.mp4"
    dummy_video.write_bytes(b"dummy video data 1080x1920 MP4")
    
    manager = PublishingManager(db_path=str(db_file), storage_dir=str(tmp_path / "published"))
    req = PublishRequest(
        video_path=str(dummy_video),
        title="What if Gravity Inverted?",
        description="A journey into inverted physics. #science #physics #shorts",
        tags=["science", "physics", "shorts"],
        destinations=["local"]
    )
    
    results = await manager.publish(req)
    assert len(results) == 1
    assert results[0].platform == "local"
    assert results[0].success is True
    assert results[0].url.startswith("file://")
    assert (tmp_path / "published").exists()

@pytest.mark.asyncio
async def test_publishing_destinations_parsing(tmp_path):
    db_file = tmp_path / "test_dest.db"
    init_db(str(db_file))
    
    dummy_video = tmp_path / "test_video.mp4"
    dummy_video.write_bytes(b"dummy video data")
    
    manager = PublishingManager(db_path=str(db_file), storage_dir=str(tmp_path / "published"))
    
    # Test 'both' destination resolves to youtube and tiktok
    resolved = manager.resolve_destinations("both")
    assert "youtube" in resolved
    assert "tiktok" in resolved
    
    # Without credentials, platform publishers report clear auth requirement error
    req = PublishRequest(
        video_path=str(dummy_video),
        title="Cosmic Wonders",
        description="Exploring space.",
        tags=["space"],
        destinations=["youtube"]
    )
    results = await manager.publish(req)
    assert len(results) == 1
    assert results[0].platform == "youtube"
    # When no OAuth token is connected, it should gracefully report requires_auth
    assert not results[0].success
    assert "auth" in results[0].error_message.lower() or "token" in results[0].error_message.lower()
