import os
import json
import httpx
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from backend.config import settings

YOUTUBE_TOKEN_PATH = settings.base_dir / "data" / "youtube_token.json"
CLIENT_SECRETS_PATH = settings.base_dir / "data" / "client_secrets.json"

class YouTubePublishResult(BaseModel):
    success: bool
    video_id: Optional[str] = None
    url: Optional[str] = None
    error_message: Optional[str] = None

class YouTubePublisher:
    """
    Automated publishing to YouTube Shorts via YouTube Data API v3 (google-api-python-client).
    Supports official OAuth2 workflow with stored refresh_token.
    """
    def __init__(
        self,
        token_path: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        self.token_path = Path(token_path) if token_path else YOUTUBE_TOKEN_PATH
        self.client_id = client_id or os.getenv("YOUTUBE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("YOUTUBE_CLIENT_SECRET")
        self.upload_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"

    def is_connected(self) -> bool:
        """Returns True if a valid token file exists or credentials are configured."""
        if self.token_path.exists():
            return True
        return bool(self.client_id and self.client_secret)

    async def upload_shorts_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str],
        access_token: Optional[str] = None,
        privacy_status: str = "public"
    ) -> YouTubePublishResult:
        """
        Uploads video to YouTube Shorts using google-api-python-client with stored OAuth refresh token,
        or direct resumable API upload.
        """
        if not os.path.exists(video_path):
            return YouTubePublishResult(
                success=False,
                error_message=f"Video file not found at: {video_path}"
            )

        # Ensure #Shorts is present in title and description
        if "#shorts" not in title.lower():
            title = f"{title} #Shorts"
        if "#shorts" not in description.lower():
            description = f"{description}\n\n#Shorts #science #education"

        # 1. Primary Method: Google API Python Client with stored refresh token
        if self.token_path.exists():
            return await self._upload_via_google_api_client(
                video_path=video_path,
                title=title,
                description=description,
                tags=tags,
                privacy_status=privacy_status
            )

        # 2. Secondary Method: Bearer access token upload
        if access_token and access_token not in ("mock_access_token_demo", ""):
            return await self._upload_via_bearer_token(
                video_path=video_path,
                title=title,
                description=description,
                tags=tags,
                access_token=access_token,
                privacy_status=privacy_status
            )

        return YouTubePublishResult(
            success=False,
            error_message="YouTube OAuth authentication required. Please connect your YouTube account in the settings dashboard (or place youtube_token.json in data/)."
        )

    async def _upload_via_google_api_client(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str],
        privacy_status: str = "public"
    ) -> YouTubePublishResult:
        """Uploads video using google-api-python-client with automated token refresh."""
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload

            with open(self.token_path, "r", encoding="utf-8") as f:
                token_data = json.load(f)

            creds = Credentials.from_authorized_user_info(token_data)
            
            # Auto-refresh token if expired
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(self.token_path, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())

            youtube = build("youtube", "v3", credentials=creds)

            body = {
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

            media = MediaFileUpload(
                video_path,
                mimetype="video/mp4",
                resumable=True
            )

            request = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()

            video_id = response.get("id")
            if video_id:
                return YouTubePublishResult(
                    success=True,
                    video_id=video_id,
                    url=f"https://www.youtube.com/shorts/{video_id}"
                )
            else:
                return YouTubePublishResult(
                    success=False,
                    error_message="YouTube upload succeeded but no video ID was returned."
                )

        except Exception as e:
            return YouTubePublishResult(
                success=False,
                error_message=f"Google API Client upload failed: {str(e)}"
            )

    async def _upload_via_bearer_token(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str],
        access_token: str,
        privacy_status: str = "public"
    ) -> YouTubePublishResult:
        """Resumable upload via HTTP requests with bearer token."""
        metadata = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags[:30],
                "categoryId": "27"
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
                init_res = await client.post(self.upload_url, headers=headers, json=metadata)
                if init_res.status_code not in (200, 201):
                    return YouTubePublishResult(
                        success=False,
                        error_message=f"YouTube resumable upload init failed ({init_res.status_code}): {init_res.text}"
                    )
                session_url = init_res.headers.get("Location")
                if not session_url:
                    return YouTubePublishResult(
                        success=False,
                        error_message="YouTube API did not return resumable upload session Location header."
                    )
                with open(video_path, "rb") as f:
                    video_bytes = f.read()
                upload_res = await client.put(
                    session_url,
                    headers={"Content-Type": "video/mp4"},
                    content=video_bytes
                )
                if upload_res.status_code in (200, 201):
                    data = upload_res.json()
                    vid_id = data.get("id")
                    return YouTubePublishResult(
                        success=True,
                        video_id=vid_id,
                        url=f"https://www.youtube.com/shorts/{vid_id}"
                    )
                else:
                    return YouTubePublishResult(
                        success=False,
                        error_message=f"YouTube video stream upload failed ({upload_res.status_code}): {upload_res.text}"
                    )
        except Exception as e:
            return YouTubePublishResult(
                success=False,
                error_message=f"Network error during YouTube upload: {str(e)}"
            )

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
