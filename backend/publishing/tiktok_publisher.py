import os
import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel

class TikTokPublishResult(BaseModel):
    success: bool
    publish_id: Optional[str] = None
    url: Optional[str] = None
    error_message: Optional[str] = None

class TikTokPublisher:
    """
    Handles authentication and publishing via TikTok Content Posting API v2.
    """
    def __init__(self, client_key: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_key = client_key or os.getenv("TIKTOK_CLIENT_KEY")
        self.client_secret = client_secret or os.getenv("TIKTOK_CLIENT_SECRET")
        self.init_url = "https://open.tiktokapis.com/v2/post/publish/video/init/"

    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refreshes expired TikTok creator access token."""
        if not self.client_key or not self.client_secret:
            return None
            
        endpoint = "https://open.tiktokapis.com/v2/oauth/token/"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(endpoint, headers=headers, data=payload)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                return {
                    "access_token": data.get("access_token"),
                    "refresh_token": data.get("refresh_token"),
                    "expires_in": data.get("expires_in", 86400),
                    "expiry": datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 86400))
                }
        return None

    async def publish_video(
        self,
        video_path: str,
        caption: str,
        access_token: Optional[str],
        privacy_level: str = "PUBLIC_TO_EVERYONE"
    ) -> TikTokPublishResult:
        """
        Initiates and uploads short-form video to TikTok Creator account.
        """
        if not access_token:
            return TikTokPublishResult(
                success=False,
                error_message="TikTok OAuth authentication required. Please connect your TikTok account in the settings dashboard."
            )
            
        if not os.path.exists(video_path):
            return TikTokPublishResult(
                success=False,
                error_message=f"Video file not found at: {video_path}"
            )
            
        video_size = os.path.getsize(video_path)
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        
        post_info = {
            "title": caption[:150],
            "privacy_level": privacy_level,
            "disable_duet": False,
            "disable_stitch": False,
            "disable_comment": False,
            "video_cover_timestamp_ms": 1000
        }
        
        source_info = {
            "source": "FILE_UPLOAD",
            "video_size": video_size,
            "chunk_size": video_size,
            "total_chunk_count": 1
        }
        
        body = {
            "post_info": post_info,
            "source_info": source_info
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                init_res = await client.post(self.init_url, headers=headers, json=body)
                if init_res.status_code != 200:
                    return TikTokPublishResult(
                        success=False,
                        error_message=f"TikTok publish init failed ({init_res.status_code}): {init_res.text}"
                    )
                    
                data = init_res.json().get("data", {})
                publish_id = data.get("publish_id")
                upload_url = data.get("upload_url")
                
                if not upload_url:
                    return TikTokPublishResult(
                        success=False,
                        error_message="TikTok API did not return an upload_url."
                    )
                    
                with open(video_path, "rb") as f:
                    content = f.read()
                    
                upload_headers = {
                    "Content-Type": "video/mp4",
                    "Content-Range": f"bytes 0-{video_size - 1}/{video_size}"
                }
                
                upload_res = await client.put(upload_url, headers=upload_headers, content=content)
                if upload_res.status_code in (200, 201):
                    return TikTokPublishResult(
                        success=True,
                        publish_id=publish_id,
                        url=f"https://www.tiktok.com/@creator/video/{publish_id}"
                    )
                else:
                    return TikTokPublishResult(
                        success=False,
                        error_message=f"TikTok upload failed ({upload_res.status_code}): {upload_res.text}"
                    )
        except Exception as e:
            return TikTokPublishResult(
                success=False,
                error_message=f"Network error during TikTok upload: {str(e)}"
            )
