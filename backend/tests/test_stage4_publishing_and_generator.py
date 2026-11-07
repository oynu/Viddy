import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from backend.media.video_generator import Procedural3DVideoGenerator
from backend.publishing.tiktok_publisher import TikTokPublisher, TikTokPublishResult
from backend.publishing.youtube_publisher import YouTubePublisher, YouTubePublishResult
from backend.publishing.tiktok_auth import save_pasted_cookies, has_saved_tiktok_cookies, TIKTOK_COOKIES_PATH

def test_video_generator_frame_rendering():
    gen = Procedural3DVideoGenerator(width=270, height=480, fps=30)
    frame = gen.render_frame(
        category="astronomy",
        t_normalized=0.2,
        current_time_sec=1.0,
        title_text="What if Earth's Gravity Doubled?"
    )
    assert frame is not None
    assert frame.size == (270, 480)

@pytest.mark.asyncio
async def test_tiktok_publisher_no_cookies(tmp_path):
    pub = TikTokPublisher(cookies_path=str(tmp_path / "nonexistent_cookies.json"))
    res = await pub.publish_video(
        video_path="output/nonexistent.mp4",
        caption="Test caption #fyp"
    )
    assert res.success is False
    assert "not found" in res.error_message.lower()

@pytest.mark.asyncio
async def test_tiktok_publisher_playwright_mock(tmp_path):
    cookies_file = tmp_path / "test_cookies.json"
    cookies_file.write_text(json.dumps([{"name": "sessionid", "value": "xyz123"}]), encoding="utf-8")
    
    mock_video = tmp_path / "test.mp4"
    mock_video.write_bytes(b"dummy mp4 data")
    
    pub = TikTokPublisher(cookies_path=str(cookies_file))
    
    with patch.object(pub, "_publish_via_playwright", new_callable=AsyncMock) as mock_pw:
        mock_pw.return_value = TikTokPublishResult(
            success=True,
            publish_id="pw_123",
            url="https://www.tiktok.com/tiktokstudio/manage"
        )
        res = await pub.publish_video(
            video_path=str(mock_video),
            caption="Test #Shorts #fyp"
        )
        assert res.success is True
        assert res.publish_id == "pw_123"
        mock_pw.assert_called_once()

@pytest.mark.asyncio
async def test_youtube_shorts_publisher_formatting(tmp_path):
    token_file = tmp_path / "youtube_token.json"
    pub = YouTubePublisher(token_path=str(token_file))
    
    mock_video = tmp_path / "test.mp4"
    mock_video.write_bytes(b"dummy mp4 data")
    
    with patch.object(pub, "_upload_via_google_api_client", new_callable=AsyncMock) as mock_upload:
        mock_upload.return_value = YouTubePublishResult(
            success=True,
            video_id="yt_short_123",
            url="https://www.youtube.com/shorts/yt_short_123"
        )
        # Mock token exists
        token_file.write_text(json.dumps({"token": "fake_token"}), encoding="utf-8")
        
        res = await pub.upload_shorts_video(
            video_path=str(mock_video),
            title="How Black Holes Warp Space",
            description="Detailed science explanation",
            tags=["science", "blackhole"]
        )
        assert res.success is True
        assert "shorts/yt_short_123" in res.url
        mock_upload.assert_called_once()
        
        # Verify #Shorts was injected into arguments passed to _upload_via_google_api_client
        call_kwargs = mock_upload.call_args[1]
        assert "#Shorts" in call_kwargs["title"]
        assert "#Shorts" in call_kwargs["description"]

def test_tiktok_cookie_helper(tmp_path):
    cookies_data = [{"name": "sid", "value": "12345"}]
    with patch("backend.publishing.tiktok_auth.TIKTOK_COOKIES_PATH", tmp_path / "cookies.json"):
        save_res = save_pasted_cookies(json.dumps(cookies_data))
        assert save_res["success"] is True
        assert (tmp_path / "cookies.json").exists()
