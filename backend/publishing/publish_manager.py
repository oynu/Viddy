import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
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
    tiktok_caption: Optional[str] = None
    tiktok_hashtags: Optional[str] = None
    tiktok_commentary: Optional[str] = None
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

    async def get_valid_token(self, platform: str) -> Optional[str]:
        """
        Retrieves active OAuth access token with automated refresh guard.
        If expired or near expiry (within 5 min buffer), invokes platform refresh endpoint
        and saves updated token to persistent database.
        """
        if not self.db_path:
            return None
            
        with get_db(self.db_path) as session:
            acc = crud.get_platform_account(session, platform)
            if not acc or not acc.is_connected:
                return None
                
            now = datetime.now(timezone.utc)
            needs_refresh = False
            
            # Check if expiry is present and within 5 minutes of expiring
            if acc.token_expiry:
                expiry = acc.token_expiry
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                if expiry <= now + timedelta(minutes=5):
                    needs_refresh = True
            elif not acc.access_token:
                needs_refresh = True
                
            if needs_refresh and acc.refresh_token:
                publisher = self.youtube_pub if platform == "youtube" else self.tiktok_pub
                renewed = await publisher.refresh_access_token(acc.refresh_token)
                if renewed and renewed.get("access_token"):
                    acc = crud.upsert_platform_account(
                        session=session,
                        platform=platform,
                        access_token=renewed["access_token"],
                        refresh_token=renewed.get("refresh_token") or acc.refresh_token,
                        token_expiry=renewed.get("expiry")
                    )
                    crud.add_log(session, f"Refreshed OAuth access token for {platform}.", stage="PUBLISH", level="INFO")
                    return acc.access_token
                    
            return acc.access_token

    async def publish(self, req: PublishRequest) -> List[PublishResult]:
        """
        Executes parallel or sequential publishing across all configured target destinations.
        Guarantees token freshness before network transmission.
        """
        results: List[PublishResult] = []
        
        target_platforms = set()
        for d in req.destinations:
            for p in self.resolve_destinations(d):
                target_platforms.add(p)

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
                token = await self.get_valid_token("youtube")
                res = await self.youtube_pub.upload_shorts_video(
                    video_path=req.video_path,
                    title=req.title,
                    description=req.description,
                    tags=req.tags,
                    access_token=token
                )
                results.append(PublishResult(
                    platform="youtube",
                    success=res.success,
                    url=res.url,
                    error_message=res.error_message
                ))
            elif platform == "tiktok":
                token = await self.get_valid_token("tiktok")
                base_caption = req.tiktok_caption or req.title
                tags_str = req.tiktok_hashtags or " ".join(req.tags[:8])
                full_caption = f"{base_caption}\n\n{tags_str}".strip()
                res = await self.tiktok_pub.publish_video(
                    video_path=req.video_path,
                    caption=full_caption,
                    access_token=token,
                    comment_text=req.tiktok_commentary
                )
                results.append(PublishResult(
                    platform="tiktok",
                    success=res.success,
                    url=res.url,
                    error_message=res.error_message
                ))
                
        return results
