import os
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database import crud
from backend.database.models import SettingModel, VideoModel, JobModel, PlatformAccountModel, LogEntryModel

router = APIRouter(prefix="/api")

# Schemas
class SettingsUpdateRequest(BaseModel):
    running_mode: Optional[str] = None
    publish_destination: Optional[str] = None
    max_daily_videos: Optional[int] = None
    cycle_delay_seconds: Optional[int] = None
    target_duration_seconds: Optional[int] = None
    default_voice: Optional[str] = None
    ai_provider: Optional[str] = None

class PlatformConnectRequest(BaseModel):
    platform: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    account_name: Optional[str] = None

# We inject worker reference dynamically from main
_worker_instance = None

def set_worker(worker):
    global _worker_instance
    _worker_instance = worker

def get_worker():
    return _worker_instance

# Agent Controls
@router.get("/agent/status")
def get_agent_status():
    worker = get_worker()
    state = worker.state.value if worker else "STOPPED"
    stage = worker.current_stage.value if worker else "IDLE"
    progress = worker.progress if worker else 0.0
    action = worker.current_action if worker else "Ready"
    
    with get_db() as session:
        settings = crud.get_settings(session)
        recent_videos = crud.get_all_videos(session, limit=100)
        
        total_created = len(recent_videos)
        total_published = len([v for v in recent_videos if v.published_destinations != "none"])
        yt_count = len([v for v in recent_videos if v.youtube_url])
        tt_count = len([v for v in recent_videos if v.tiktok_url])
        failed_count = len([v for v in recent_videos if v.status == "failed"])
        
        active_job = crud.get_active_job(session)
        current_job_dict = None
        if active_job:
            current_job_dict = {
                "id": active_job.id,
                "stage": active_job.stage,
                "progress": active_job.progress,
                "current_action": active_job.current_action,
                "video_id": active_job.video_id
            }

        return {
            "state": state,
            "stage": stage,
            "progress": progress,
            "current_action": action,
            "current_job": current_job_dict,
            "stats": {
                "total_created": total_created,
                "total_published": total_published,
                "youtube_published": yt_count,
                "tiktok_published": tt_count,
                "failed_count": failed_count,
                "daily_produced": settings.daily_videos_produced,
                "daily_limit": settings.max_daily_videos
            },
            "settings": {
                "running_mode": settings.running_mode,
                "publish_destination": settings.publish_destination,
                "max_daily_videos": settings.max_daily_videos,
                "cycle_delay_seconds": settings.cycle_delay_seconds,
                "default_voice": settings.default_voice
            }
        }

@router.post("/agent/start")
async def start_agent():
    worker = get_worker()
    if not worker:
        raise HTTPException(status_code=500, detail="Worker instance not initialized")
    await worker.start()
    return {"message": "Autonomous production loop started", "state": worker.state.value}

@router.post("/agent/pause")
async def pause_agent():
    worker = get_worker()
    if not worker:
        raise HTTPException(status_code=500, detail="Worker instance not initialized")
    await worker.pause()
    return {"message": "Agent suspended", "state": worker.state.value}

@router.post("/agent/resume")
async def resume_agent():
    worker = get_worker()
    if not worker:
        raise HTTPException(status_code=500, detail="Worker instance not initialized")
    await worker.resume()
    return {"message": "Agent resumed", "state": worker.state.value}

@router.post("/agent/stop")
async def stop_agent():
    worker = get_worker()
    if not worker:
        raise HTTPException(status_code=500, detail="Worker instance not initialized")
    await worker.stop()
    return {"message": "Agent stopped", "state": worker.state.value}

# Settings
@router.get("/settings")
def get_system_settings():
    with get_db() as session:
        st = crud.get_settings(session)
        return {
            "id": st.id,
            "running_mode": st.running_mode,
            "publish_destination": st.publish_destination,
            "max_daily_videos": st.max_daily_videos,
            "daily_videos_produced": st.daily_videos_produced,
            "cycle_delay_seconds": st.cycle_delay_seconds,
            "target_duration_seconds": st.target_duration_seconds,
            "default_voice": st.default_voice,
            "ai_provider": st.ai_provider
        }

@router.post("/settings")
def update_system_settings(req: SettingsUpdateRequest):
    with get_db() as session:
        updates = req.model_dump(exclude_unset=True)
        st = crud.update_settings(session, **updates)
        return {
            "id": st.id,
            "running_mode": st.running_mode,
            "publish_destination": st.publish_destination,
            "max_daily_videos": st.max_daily_videos,
            "daily_videos_produced": st.daily_videos_produced,
            "cycle_delay_seconds": st.cycle_delay_seconds,
            "target_duration_seconds": st.target_duration_seconds,
            "default_voice": st.default_voice,
            "ai_provider": st.ai_provider
        }

# Video Library
@router.get("/videos")
def list_videos(limit: int = 50):
    with get_db() as session:
        videos = crud.get_all_videos(session, limit=limit)
        return [
            {
                "id": v.id,
                "title": v.title,
                "topic": v.topic,
                "category": v.category,
                "script": v.script,
                "hook": v.hook,
                "duration": v.duration,
                "status": v.status,
                "video_path": v.video_path,
                "thumbnail_path": v.thumbnail_path,
                "published_destinations": v.published_destinations,
                "youtube_url": v.youtube_url,
                "tiktok_url": v.tiktok_url,
                "tiktok_commentary": v.tiktok_commentary,
                "tiktok_hashtags": v.tiktok_hashtags,
                "youtube_tags": v.youtube_tags,
                "qc_passed": v.qc_passed,
                "created_at": v.created_at.isoformat() if v.created_at else None
            }
            for v in videos
        ]

@router.get("/videos/{video_id}")
def get_video_detail(video_id: int):
    with get_db() as session:
        v = crud.get_video_by_id(session, video_id)
        if not v:
            raise HTTPException(status_code=404, detail="Video not found")
        return {
            "id": v.id,
            "title": v.title,
            "topic": v.topic,
            "category": v.category,
            "script": v.script,
            "hook": v.hook,
            "duration": v.duration,
            "status": v.status,
            "video_path": v.video_path,
            "thumbnail_path": v.thumbnail_path,
            "subtitle_path": v.subtitle_path,
            "published_destinations": v.published_destinations,
            "youtube_url": v.youtube_url,
            "tiktok_url": v.tiktok_url,
            "tiktok_commentary": v.tiktok_commentary,
            "tiktok_hashtags": v.tiktok_hashtags,
            "youtube_tags": v.youtube_tags,
            "qc_passed": v.qc_passed,
            "qc_details": v.qc_details,
            "error_message": v.error_message,
            "created_at": v.created_at.isoformat() if v.created_at else None
        }

class AutoPublishRequest(BaseModel):
    destination: str = "tiktok"

@router.post("/videos/{video_id}/auto-publish")
async def auto_publish_video_endpoint(video_id: int, req: Optional[AutoPublishRequest] = None):
    worker = get_worker()
    dest = (req.destination if req else "tiktok").lower()
    
    with get_db() as session:
        v = crud.get_video_by_id(session, video_id)
        if not v:
            raise HTTPException(status_code=404, detail="Video not found")
        if not v.video_path or not os.path.exists(v.video_path):
            raise HTTPException(status_code=400, detail="Video file does not exist on disk")

        from backend.publishing.publish_manager import PublishRequest, PublishingManager
        pub_req = PublishRequest(
            video_path=v.video_path,
            title=v.title,
            description=v.script,
            tags=v.youtube_tags.split(",") if v.youtube_tags else ["science", "education"],
            tiktok_caption=v.title,
            tiktok_hashtags=v.tiktok_hashtags,
            tiktok_commentary=v.tiktok_commentary,
            thumbnail_path=v.thumbnail_path,
            destinations=[dest]
        )
        
        pub_mgr = worker.publish_mgr if worker else PublishingManager()
        results = await pub_mgr.publish(pub_req)
        
        successful = [r for r in results if r.success]
        if successful:
            v.status = "published"
            v.published_destinations = ",".join(list(set(filter(None, [v.published_destinations, dest]))))
            for r in successful:
                if r.platform == "tiktok" and r.url:
                    v.tiktok_url = r.url
                elif r.platform == "youtube" and r.url:
                    v.youtube_url = r.url
            session.commit()
            return {"success": True, "message": f"Successfully published to {dest}!", "results": [r.model_dump(mode='json') for r in results]}
        else:
            errors = [r.error_message for r in results if r.error_message]
            err_msg = "; ".join(errors) if errors else "Publishing failed. Check channel credentials."
            return {"success": False, "message": err_msg, "results": [r.model_dump(mode='json') for r in results]}

class VideoUpdateRequest(BaseModel):
    title: Optional[str] = None
    script: Optional[str] = None
    tiktok_hashtags: Optional[str] = None
    tiktok_commentary: Optional[str] = None
    youtube_tags: Optional[str] = None

@router.post("/videos/upload")
async def upload_videos_endpoint(
    files: List[UploadFile] = File(...),
    destination: str = Form("tiktok")
):
    from pathlib import Path
    import uuid
    import re
    from backend.config import settings
    from backend.publishing.video_prober import probe_video_metadata, generate_video_thumbnail

    upload_dir = settings.base_dir / "output" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    created_videos = []

    with get_db() as session:
        for f in files:
            orig_filename = f.filename or "video.mp4"
            clean_stem = Path(orig_filename).stem
            clean_title = re.sub(r"[_\-\.]+", " ", clean_stem).strip().title()
            if not clean_title:
                clean_title = "Uploaded Short Video"

            unique_id = uuid.uuid4().hex[:8]
            safe_filename = f"{unique_id}_{Path(orig_filename).name}"
            saved_path = upload_dir / safe_filename
            thumb_path = upload_dir / f"{unique_id}_thumb.jpg"

            with open(saved_path, "wb") as buffer:
                while chunk := await f.read(1024 * 1024):
                    buffer.write(chunk)

            meta = probe_video_metadata(str(saved_path))
            generate_video_thumbnail(str(saved_path), str(thumb_path))

            default_hashtags = "#fyp #foryou #viral #trending #shorts #creator"
            default_commentary = "What did you think about this? Drop your thoughts below! 👇"

            video = crud.create_video(
                session=session,
                title=clean_title,
                topic="Uploaded",
                category="custom",
                script=clean_title,
                hook=clean_title,
                status="ready"
            )
            video.video_path = str(saved_path.resolve())
            video.thumbnail_path = str(thumb_path.resolve()) if thumb_path.exists() else None
            video.duration = meta.get("duration", 0.0)
            video.tiktok_hashtags = default_hashtags
            video.tiktok_commentary = default_commentary
            video.youtube_tags = "shorts,viral,trending,custom"
            session.commit()

            created_videos.append({
                "id": video.id,
                "title": video.title,
                "duration": video.duration,
                "status": video.status,
                "video_path": video.video_path,
                "thumbnail_path": video.thumbnail_path,
                "tiktok_hashtags": video.tiktok_hashtags,
                "tiktok_commentary": video.tiktok_commentary,
                "created_at": video.created_at.isoformat() if video.created_at else None
            })

    return {"success": True, "count": len(created_videos), "videos": created_videos}

@router.delete("/videos/{video_id}")
def delete_video_endpoint(video_id: int):
    with get_db() as session:
        v = crud.get_video_by_id(session, video_id)
        if not v:
            raise HTTPException(status_code=404, detail="Video not found")
        try:
            if v.video_path and os.path.exists(v.video_path) and "output/uploads" in v.video_path.replace("\\", "/"):
                os.remove(v.video_path)
            if v.thumbnail_path and os.path.exists(v.thumbnail_path):
                os.remove(v.thumbnail_path)
        except Exception:
            pass
        session.delete(v)
        session.commit()
        return {"success": True, "message": f"Video {video_id} deleted"}

@router.patch("/videos/{video_id}")
def update_video_endpoint(video_id: int, req: VideoUpdateRequest):
    with get_db() as session:
        v = crud.get_video_by_id(session, video_id)
        if not v:
            raise HTTPException(status_code=404, detail="Video not found")
        if req.title is not None:
            v.title = req.title
        if req.script is not None:
            v.script = req.script
        if req.tiktok_hashtags is not None:
            v.tiktok_hashtags = req.tiktok_hashtags
        if req.tiktok_commentary is not None:
            v.tiktok_commentary = req.tiktok_commentary
        if req.youtube_tags is not None:
            v.youtube_tags = req.youtube_tags
        session.commit()
        return {"success": True, "message": f"Video {video_id} updated"}

class MetadataGenRequest(BaseModel):
    prompt: Optional[str] = None

@router.post("/videos/{video_id}/auto-metadata")
def auto_generate_video_metadata_endpoint(video_id: int, req: Optional[MetadataGenRequest] = None):
    from backend.publishing.metadata_generator import generate_smart_metadata
    with get_db() as session:
        v = crud.get_video_by_id(session, video_id)
        if not v:
            raise HTTPException(status_code=404, detail="Video not found")
        prompt = req.prompt if req else None
        meta = generate_smart_metadata(raw_title=v.title, prompt=prompt)
        v.title = meta["title"]
        v.tiktok_hashtags = meta["tiktok_hashtags"]
        v.tiktok_commentary = meta["tiktok_commentary"]
        v.youtube_tags = meta["youtube_tags"]
        v.script = meta["youtube_description"]
        session.commit()
        return {
            "success": True,
            "message": "Metadata generated successfully",
            "video": {
                "id": v.id,
                "title": v.title,
                "tiktok_hashtags": v.tiktok_hashtags,
                "tiktok_commentary": v.tiktok_commentary,
                "youtube_tags": v.youtube_tags,
                "script": v.script
            }
        }

@router.post("/videos/auto-metadata-all")
def auto_generate_all_metadata_endpoint():
    from backend.publishing.metadata_generator import generate_smart_metadata
    with get_db() as session:
        videos = session.query(VideoModel).filter(VideoModel.status.in_(["ready", "queued", "pending"])).all()
        updated_count = 0
        for v in videos:
            meta = generate_smart_metadata(raw_title=v.title)
            v.title = meta["title"]
            v.tiktok_hashtags = meta["tiktok_hashtags"]
            v.tiktok_commentary = meta["tiktok_commentary"]
            v.youtube_tags = meta["youtube_tags"]
            v.script = meta["youtube_description"]
            updated_count += 1
        session.commit()
        return {"success": True, "count": updated_count, "message": f"Updated metadata for {updated_count} videos"}

# Platform Accounts & Connections
class TikTokCookiesPayload(BaseModel):
    cookies_json: str

class YouTubeTokenPayload(BaseModel):
    token_json: str

@router.get("/channels")
def get_channels():
    import json
    from backend.publishing.tiktok_auth import has_saved_tiktok_cookies, TIKTOK_COOKIES_PATH
    from backend.publishing.youtube_publisher import YOUTUBE_TOKEN_PATH
    with get_db() as session:
        yt = crud.get_platform_account(session, "youtube")
        tt = crud.get_platform_account(session, "tiktok")
        
        tt_connected = has_saved_tiktok_cookies() or (tt.is_connected if tt else False)
        yt_connected = YOUTUBE_TOKEN_PATH.exists() or (yt.is_connected if yt else False)
        
        return {
            "youtube": {
                "connected": yt_connected,
                "account_name": yt.account_name if yt and yt.account_name else ("YouTube Shorts (OAuth Active)" if YOUTUBE_TOKEN_PATH.exists() else None),
                "channel_id": yt.channel_id if yt else None,
                "token_expiry": yt.token_expiry.isoformat() if yt and yt.token_expiry else None
            },
            "tiktok": {
                "connected": tt_connected,
                "account_name": tt.account_name if tt and tt.account_name else ("TikTok (cookies.json Active)" if has_saved_tiktok_cookies() else None),
                "channel_id": tt.channel_id if tt else None,
                "token_expiry": tt.token_expiry.isoformat() if tt and tt.token_expiry else None
            }
        }

@router.post("/channels/tiktok/cookies")
def save_tiktok_cookies_route(payload: TikTokCookiesPayload):
    from backend.publishing.tiktok_auth import save_pasted_cookies
    res = save_pasted_cookies(payload.cookies_json)
    if res.get("success"):
        with get_db() as session:
            crud.upsert_platform_account(session, "tiktok", is_connected=True, account_name="TikTok Account (cookies.json)")
    return res

@router.post("/channels/tiktok/login-browser")
async def trigger_tiktok_browser_login():
    from backend.publishing.tiktok_auth import launch_interactive_tiktok_login
    async def _safe_login():
        try:
            await launch_interactive_tiktok_login(headless=False)
        except Exception as e:
            with get_db() as s:
                crud.add_log(s, f"TikTok Brave login error: {str(e)}", stage="PUBLISH", level="ERROR")
    asyncio.create_task(_safe_login())
    return {"message": "TikTok login window launched. Please sign in on the browser window to save your session."}

@router.post("/channels/youtube/token")
def save_youtube_token_route(payload: YouTubeTokenPayload):
    import json
    from backend.publishing.youtube_publisher import YOUTUBE_TOKEN_PATH
    try:
        data = json.loads(payload.token_json.strip())
        YOUTUBE_TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(YOUTUBE_TOKEN_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        with get_db() as session:
            crud.upsert_platform_account(session, "youtube", is_connected=True, account_name="YouTube Shorts (OAuth Active)")
        return {"success": True, "message": "YouTube token saved successfully."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/channels/connect")
def connect_channel(req: PlatformConnectRequest):
    with get_db() as session:
        acc = crud.upsert_platform_account(
            session=session,
            platform=req.platform,
            is_connected=True,
            access_token=req.access_token or "mock_access_token_demo",
            refresh_token=req.refresh_token or "mock_refresh_token_demo",
            account_name=req.account_name or f"Authorized {req.platform.capitalize()} Creator"
        )
        return {
            "message": f"Successfully connected {req.platform}",
            "platform": acc.platform,
            "connected": acc.is_connected,
            "account_name": acc.account_name
        }

@router.post("/channels/disconnect")
def disconnect_channel(platform: str):
    with get_db() as session:
        acc = crud.upsert_platform_account(
            session=session,
            platform=platform,
            is_connected=False,
            access_token=None,
            refresh_token=None,
            account_name=None
        )
        return {"message": f"Disconnected {platform}", "connected": False}

# Real-time System Logs
@router.get("/logs")
def get_logs(limit: int = 100):
    with get_db() as session:
        logs = crud.get_recent_logs(session, limit=limit)
        return [
            {
                "id": l.id,
                "level": l.level,
                "stage": l.stage,
                "message": l.message,
                "created_at": l.created_at.isoformat() if l.created_at else None
            }
            for l in logs
        ]
