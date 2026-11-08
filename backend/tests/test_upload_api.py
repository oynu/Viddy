import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.publishing.video_prober import probe_video_metadata, generate_video_thumbnail

def test_probe_video_metadata_on_missing_file():
    info = probe_video_metadata("nonexistent_video.mp4")
    assert info["duration"] == 0.0
    assert info["width"] == 0
    assert info["height"] == 0

def test_upload_single_video_endpoint(tmp_path):
    dummy_video_path = tmp_path / "my_cool_short.mp4"
    dummy_video_path.write_bytes(b"fake mp4 content for testing")

    with TestClient(app) as client:
        with open(dummy_video_path, "rb") as f:
            response = client.post(
                "/api/videos/upload",
                files=[("files", ("my_cool_short.mp4", f, "video/mp4"))],
                data={"destination": "tiktok"}
            )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["videos"]) == 1
        video = data["videos"][0]
        v_id = video["id"]
        assert "my cool short" in video["title"].lower()
        assert video["status"] in ["ready", "queued"]
        assert os.path.exists(video["video_path"])

        # Test update video
        patch_res = client.patch(
            f"/api/videos/{v_id}",
            json={"title": "Updated Cool Short Title", "tiktok_hashtags": "#updated #fyp"}
        )
        assert patch_res.status_code == 200

        # Test delete video
        del_res = client.delete(f"/api/videos/{v_id}")
        assert del_res.status_code == 200
