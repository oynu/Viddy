import pytest
from fastapi.testclient import TestClient
from backend.main import app

def test_api_status_and_controls():
    with TestClient(app) as client:
        # 1. Check status endpoint
        response = client.get("/api/agent/status")
        assert response.status_code == 200
        data = response.json()
        assert "state" in data
        assert "stage" in data
        assert "stats" in data
        assert "settings" in data

        # 2. Check settings update
        update_res = client.post("/api/settings", json={
            "running_mode": "continuous",
            "publish_destination": "local",
            "max_daily_videos": 12,
            "cycle_delay_seconds": 15
        })
        assert update_res.status_code == 200
        updated_data = update_res.json()
        assert updated_data["publish_destination"] == "local"
        assert updated_data["max_daily_videos"] == 12

        # 3. Check videos listing
        videos_res = client.get("/api/videos")
        assert videos_res.status_code == 200
        assert isinstance(videos_res.json(), list)

        # 4. Check platform channels
        channels_res = client.get("/api/channels")
        assert channels_res.status_code == 200
        channels = channels_res.json()
        assert "youtube" in channels
        assert "tiktok" in channels

        # 5. Check logs listing
        logs_res = client.get("/api/logs")
        assert logs_res.status_code == 200
        assert isinstance(logs_res.json(), list)
