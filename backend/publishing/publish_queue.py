import os
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from backend.config import settings
from backend.publishing.publish_manager import PublishRequest, PublishingManager, PublishResult
from backend.publishing.browser_utils import clean_stale_profile_locks
from backend.database.session import get_db
from backend.database import crud

class QueueItem(BaseModel):
    video_id: int
    destination: str = "tiktok"
    title: str
    video_path: str
    description: Optional[str] = None
    tiktok_caption: Optional[str] = None
    tiktok_hashtags: Optional[str] = None
    tiktok_commentary: Optional[str] = None
    youtube_tags: Optional[str] = None
    thumbnail_path: Optional[str] = None
    status: str = "queued"
    error_message: Optional[str] = None

class PublishQueue:
    """
    Asynchronous FIFO publishing queue for batch video uploads to TikTok, YouTube Shorts, or Both.
    Processes items sequentially to avoid browser lock contention and platform rate issues.
    """
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self._items: List[QueueItem] = []
        self._active_item: Optional[QueueItem] = None
        self._is_running: bool = False
        self._task: Optional[asyncio.Task] = None
        self.completed_count: int = 0
        self.failed_count: int = 0

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def queue_length(self) -> int:
        return len(self._items)

    def add_item(self, item: QueueItem):
        self._items.append(item)

    def clear(self):
        self._items.clear()
        self._active_item = None

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_running": self._is_running,
            "queued_count": len(self._items),
            "completed_count": self.completed_count,
            "failed_count": self.failed_count,
            "active_item": self._active_item.model_dump() if self._active_item else None,
            "queue": [i.model_dump() for i in self._items]
        }

    def enqueue_db_videos(self, video_ids: List[int], destination: str = "tiktok") -> int:
        """Loads video details from database and appends to publish queue."""
        added = 0
        with get_db(self.db_path) as session:
            for vid in video_ids:
                v = crud.get_video_by_id(session, vid)
                if not v or not v.video_path or not os.path.exists(v.video_path):
                    continue
                # Don't duplicate if already in queue
                if any(i.video_id == vid for i in self._items):
                    continue

                item = QueueItem(
                    video_id=v.id,
                    destination=destination,
                    title=v.title,
                    video_path=v.video_path,
                    description=v.script,
                    tiktok_caption=v.title,
                    tiktok_hashtags=v.tiktok_hashtags,
                    tiktok_commentary=v.tiktok_commentary,
                    youtube_tags=v.youtube_tags,
                    thumbnail_path=v.thumbnail_path
                )
                self.add_item(item)
                v.status = "queued"
                added += 1
            session.commit()
        return added

    async def process_one(self) -> bool:
        """Processes the single next item in the queue."""
        if not self._items:
            self._active_item = None
            return False

        item = self._items.pop(0)
        self._active_item = item
        item.status = "publishing"

        # Update DB status
        with get_db(self.db_path) as session:
            crud.update_video(session, item.video_id, status="publishing")
            crud.add_log(session, f"Starting publish queue for '{item.title}' -> {item.destination.upper()}...", stage="PUBLISH", level="INFO")

        # Clean lingering profile locks before launch
        clean_stale_profile_locks(settings.base_dir / "data" / "tiktok_user_data")

        # Prepare destinations
        dest = item.destination.lower()
        target_destinations = ["tiktok", "youtube"] if dest == "both" else [dest]

        pub_req = PublishRequest(
            video_path=item.video_path,
            title=item.title,
            description=item.description or item.title,
            tags=item.youtube_tags.split(",") if item.youtube_tags else ["shorts", "viral"],
            tiktok_caption=item.tiktok_caption or item.title,
            tiktok_hashtags=item.tiktok_hashtags,
            tiktok_commentary=item.tiktok_commentary,
            thumbnail_path=item.thumbnail_path,
            destinations=target_destinations
        )

        pub_mgr = PublishingManager(db_path=self.db_path)
        try:
            results = await pub_mgr.publish(pub_req)
        except Exception as e:
            results = [PublishResult(platform=dest, success=False, error_message=str(e))]

        # Evaluate outcome
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        if successful:
            self.completed_count += 1
        else:
            self.failed_count += 1

        with get_db(self.db_path) as session:
            v = crud.get_video_by_id(session, item.video_id)
            if v:
                if successful:
                    v.status = "published"
                    v.completed_at = datetime.now(timezone.utc)
                    v.published_destinations = ",".join(list(set(filter(None, [v.published_destinations] + [r.platform for r in successful]))))
                    for r in successful:
                        if r.platform == "tiktok" and r.url:
                            v.tiktok_url = r.url
                        elif r.platform == "youtube" and r.url:
                            v.youtube_url = r.url
                    crud.add_log(session, f"Successfully published '{item.title}' to {[r.platform for r in successful]}.", stage="PUBLISH", level="SUCCESS")
                else:
                    v.status = "failed"
                    v.error_message = "; ".join([r.error_message for r in failed if r.error_message]) or "Publishing failed"
                    crud.add_log(session, f"Failed publishing '{item.title}': {v.error_message}", stage="PUBLISH", level="ERROR")
                session.commit()

        # Clean locks after each post so the next item has a clean browser state
        clean_stale_profile_locks(settings.base_dir / "data" / "tiktok_user_data")
        self._active_item = None
        return len(successful) > 0

    async def _queue_loop(self):
        """Sequential execution loop."""
        self._is_running = True
        try:
            while self._is_running and len(self._items) > 0:
                await self.process_one()
                if len(self._items) > 0:
                    await asyncio.sleep(4.0)
        finally:
            self._is_running = False
            self._active_item = None

    def start(self):
        """Starts asynchronous queue worker."""
        if self._is_running and self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._queue_loop())

    def stop(self):
        """Stops queue worker after current item finishes."""
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()

# Global singleton
_publish_queue_instance: Optional[PublishQueue] = None

def get_publish_queue() -> PublishQueue:
    global _publish_queue_instance
    if _publish_queue_instance is None:
        _publish_queue_instance = PublishQueue()
    return _publish_queue_instance
