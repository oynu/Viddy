import os
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from backend.publishing.local_publisher import LocalPublisher
from backend.publishing.youtube_publisher import YouTubePublisher
from backend.publishing.tiktok_publisher import TikTokPublisher
from backend.database.session import get_db
from backend.database import crud

class PublishRequest(BaseModel):
    video_path: str
    title: str
    description: str
    tags: List[str] = Field(default_factory=list)
    thumbnail_path: Optional[str] = None
    destinations: List[str] = Field(default_factory=lambda: ["local"])

class PublishResult(BaseModel):
    platform: str
    success: bool
    url: Optional[str] = None
    error_message: Optional[str] = None
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PublishingManager:
    def __init__(self, db_path: Optional[str] = None, storage_dir: str = "output/published"):
        self.db_path = db_path
        self.local_pub = LocalPublisher(base_storage_dir=storage_dir)
        self.youtube_pub = YouTubePublisher()
        self.tiktok_pub = TikTokPublisher()

    def resolve_destinations(self, configured_pref: str) -> List[str]:
        """Resolves preference string to list of target platforms."""
        pref = configured_pref.lower().strip()
        if pref == "both":
            return ["youtube", "tiktok"]
        elif pref in ["youtube", "tiktok", "local"]:
            return [pref]
        return ["local"]

    async def publish(self, req: PublishRequest) -> List[PublishResult]:
        """
        Executes parallel or sequential publishing across all configured target destinations.
        """
        results: List[PublishResult] = []
        
        # Expand 'both' if in request destinations
        target_platforms = set()
        for d in req.destinations:
            for p in self.resolve_destinations(d):
                target_platforms.add(p)
                
        # Retrieve credentials from SQLite if db_path provided
        yt_token = None
        tt_token = None
        if self.db_path:
            with get_db(self.db_path) as session:
                yt_acc = crud.get_platform_account(session, "youtube")
                if yt_acc and yt_acc.is_connected:
                    yt_token = yt_acc.access_token
                tt_acc = crud.get_platform_account(session, "tiktok")
                if tt_acc and tt_acc.is_connected:
                    tt_token = tt_acc.access_token

        for platform in target_platforms:
            if platform == "local":
                res = self.local_pub.publish_video(
                    video_path=req.video_path,
                    title=req.title,
                    description=req.description,
                    tags=req.tags,
                    thumbnail_path=req.thumbnail_path
                )
                results.append(PublishResult(
                    platform="local",
                    success=res.success,
                    url=res.url if res.success else None,
                    error_message=res.error_message
                ))
            elif platform == "youtube":
                res = await self.youtube_pub.upload_shorts_video(
                    video_path=req.video_path,
                    title=req.title,
                    description=req.description,
                    tags=req.tags,
                    access_token=yt_token
                )
                results.append(PublishResult(
                    platform="youtube",
                    success=res.success,
                    url=res.url,
                    error_message=res.error_message
                ))
            elif platform == "tiktok":
                res = await self.tiktok_pub.publish_video(
                    video_path=req.video_path,
                    caption=f"{req.title} {' '.join(req.tags[:4])}",
                    access_token=tt_token
                )
                results.append(PublishResult(
                    platform="tiktok",
                    success=res.success,
                    url=res.url,
                    error_message=res.error_message
                ))
                
        return results
