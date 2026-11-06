import os
import json
import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel

class YouTubePublishResult(BaseModel):
    success: bool
    video_id: Optional[str] = None
    url: Optional[str] = None
    error_message: Optional[str] = None

class YouTubePublisher:
    """
    Handles authentication and automated uploads to YouTube Shorts via YouTube Data API v3.
    Respects real OAuth2 credentials and token refresh workflows.
    """
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id or os.getenv("YOUTUBE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("YOUTUBE_CLIENT_SECRET")
        self.upload_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"

    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refreshes expired OAuth2 access token with Google Accounts."""
        if not self.client_id or not self.client_secret:
            return None
            
        token_endpoint = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(token_endpoint, data=payload)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "access_token": data.get("access_token"),
                    "expires_in": data.get("expires_in", 3600),
                    "expiry": datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 3600))
                }
        return None

    async def upload_shorts_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list,
        access_token: Optional[str],
        privacy_status: str = "public"
    ) -> YouTubePublishResult:
        """
        Uploads video to YouTube Shorts using YouTube Data API v3.
        """
        if not access_token:
            return YouTubePublishResult(
                success=False,
                error_message="YouTube OAuth authentication required. Please connect your YouTube account in the settings dashboard."
            )
            
        if not os.path.exists(video_path):
            return YouTubePublishResult(
                success=False,
                error_message=f"Video file not found at: {video_path}"
            )
            
        # Ensure #Shorts is in title/description
        if "#shorts" not in title.lower():
            title = f"{title} #Shorts"
            
        metadata = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags[:30],
                "categoryId": "27"  # Education
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(os.path.getsize(video_path))
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # 1. Initialize resumable session
                init_res = await client.post(self.upload_url, headers=headers, json=metadata)
                if init_res.status_code not in (200, 201):
                    return YouTubePublishResult(
                        success=False,
                        error_message=f"YouTube API initiation failed ({init_res.status_code}): {init_res.text}"
                    )
                    
                upload_location = init_res.headers.get("Location")
                if not upload_location:
                    return YouTubePublishResult(
                        success=False,
                        error_message="YouTube API did not return resumable upload Location."
                    )
                    
                # 2. Upload video binary
                with open(video_path, "rb") as f:
                    video_bytes = f.read()
                    
                upload_res = await client.put(
                    upload_location,
                    headers={"Content-Type": "video/mp4"},
                    content=video_bytes
                )
                
                if upload_res.status_code in (200, 201):
                    data = upload_res.json()
                    vid_id = data.get("id")
                    url = f"https://youtube.com/shorts/{vid_id}"
                    return YouTubePublishResult(
                        success=True,
                        video_id=vid_id,
                        url=url
                    )
                else:
                    return YouTubePublishResult(
                        success=False,
                        error_message=f"YouTube video upload chunk failed ({upload_res.status_code}): {upload_res.text}"
                    )
        except Exception as e:
            return YouTubePublishResult(
                success=False,
                error_message=f"Network error during YouTube upload: {str(e)}"
            )
