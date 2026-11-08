import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.publishing.publish_queue import PublishQueue, QueueItem
from backend.publishing.publish_manager import PublishResult

@pytest.mark.asyncio
async def test_publish_queue_lifecycle():
    queue = PublishQueue()
    assert queue.is_running is False
    assert queue.queue_length == 0

    item1 = QueueItem(video_id=1, destination="tiktok", title="Video 1", video_path="path/1.mp4")
    item2 = QueueItem(video_id=2, destination="both", title="Video 2", video_path="path/2.mp4")

    queue.add_item(item1)
    queue.add_item(item2)
    assert queue.queue_length == 2

    status = queue.get_status()
    assert status["queued_count"] == 2
    assert status["is_running"] is False

@pytest.mark.asyncio
async def test_publish_queue_single_execution():
    queue = PublishQueue()
    mock_pub_mgr = MagicMock()
    mock_pub_mgr.publish = AsyncMock(return_value=[
        PublishResult(platform="tiktok", success=True, url="https://tiktok.com/@me/video/123")
    ])

    item = QueueItem(
        video_id=101,
        destination="tiktok",
        title="Test Vid",
        video_path="path/test.mp4",
        tiktok_caption="Cool #fyp",
        tiktok_hashtags="#fyp #viral",
        tiktok_commentary="Drop a comment!"
    )
    queue.add_item(item)

    with patch("backend.publishing.publish_queue.PublishingManager", return_value=mock_pub_mgr):
        success = await queue.process_one()
        assert success is True
        assert queue.completed_count == 1
        assert queue.queue_length == 0

def test_queue_api_endpoints():
    with TestClient(app) as client:
        # 1. Check queue status
        res = client.get("/api/queue/status")
        assert res.status_code == 200
        data = res.json()
        assert "queued_count" in data
        assert "is_running" in data

        # 2. Check queue stop
        stop_res = client.post("/api/queue/stop")
        assert stop_res.status_code == 200
