import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.publishing.metadata_generator import generate_smart_metadata

def test_generate_smart_metadata_heuristics():
    meta = generate_smart_metadata(
        raw_title="how_quantum_computers_break_encryption.mp4",
        prompt="Explain quantum encryption"
    )
    assert meta["title"]
    assert "#fyp" in meta["tiktok_hashtags"]
    assert "#Shorts" in meta["youtube_description"]
    assert len(meta["tiktok_commentary"]) > 10
    assert "quantum" in meta["youtube_tags"].lower()

def test_auto_metadata_api_endpoint(tmp_path):
    dummy_video_path = tmp_path / "speed_of_light_paradox.mp4"
    dummy_video_path.write_bytes(b"dummy mp4 data")

    with TestClient(app) as client:
        # 1. Upload video
        with open(dummy_video_path, "rb") as f:
            up_res = client.post(
                "/api/videos/upload",
                files=[("files", ("speed_of_light_paradox.mp4", f, "video/mp4"))]
            )
        v_id = up_res.json()["videos"][0]["id"]

        # 2. Trigger auto metadata generation
        meta_res = client.post(f"/api/videos/{v_id}/auto-metadata")
        assert meta_res.status_code == 200
        data = meta_res.json()
        assert data["success"] is True
        assert data["video"]["tiktok_hashtags"]
        assert len(data["video"]["tiktok_commentary"]) > 10
