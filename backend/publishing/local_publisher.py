import os
import shutil
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel

class LocalPublishResult(BaseModel):
    success: bool
    path: str
    url: str
    metadata_path: str
    error_message: Optional[str] = None

class LocalPublisher:
    def __init__(self, base_storage_dir: str):
        self.base_storage_dir = Path(base_storage_dir)
        self.base_storage_dir.mkdir(parents=True, exist_ok=True)

    def publish_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list,
        thumbnail_path: Optional[str] = None
    ) -> LocalPublishResult:
        """
        Organizes completed production into local release directory with metadata.json.
        """
        try:
            if not os.path.exists(video_path):
                return LocalPublishResult(
                    success=False,
                    path="",
                    url="",
                    metadata_path="",
                    error_message=f"Source video file not found: {video_path}"
                )
                
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            safe_slug = re.sub(r"[^a-zA-Z0-9_\-]+", "_", title.lower())[:40].strip("_")
            folder_name = f"{timestamp}_{safe_slug}"
            release_dir = self.base_storage_dir / folder_name
            release_dir.mkdir(parents=True, exist_ok=True)
            
            # Destination video
            dest_video = release_dir / "video.mp4"
            shutil.copy2(video_path, dest_video)
            
            # Destination thumbnail
            dest_thumb = None
            if thumbnail_path and os.path.exists(thumbnail_path):
                dest_thumb = release_dir / "thumbnail.jpg"
                shutil.copy2(thumbnail_path, dest_thumb)
                
            # Metadata JSON
            meta = {
                "title": title,
                "description": description,
                "tags": tags,
                "timestamp": timestamp,
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "file_size": dest_video.stat().st_size,
                "aspect_ratio": "9:16",
                "resolution": "1080x1920"
            }
            meta_path = release_dir / "metadata.json"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)
                
            file_url = f"file:///{dest_video.resolve()}".replace("\\", "/")
            return LocalPublishResult(
                success=True,
                path=str(dest_video.resolve()),
                url=file_url,
                metadata_path=str(meta_path.resolve())
            )
        except Exception as e:
            return LocalPublishResult(
                success=False,
                path="",
                url="",
                metadata_path="",
                error_message=str(e)
            )
