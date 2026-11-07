import os
import sys
import asyncio

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable

from backend.agents.idea_discovery import IdeaDiscoveryAgent, IdeaProposal
from backend.agents.researcher import ResearchAgent, ResearchedConcept
from backend.agents.scriptwriter import ScriptwritingAgent, VideoScript
from backend.agents.visual_director import VisualDirectorAgent, VisualProductionPlan
from backend.agents.quality_control import QualityControlAgent, QCReport
from backend.blender.runner import BlenderRunner
from backend.media.audio_engine import AudioEngine
from backend.media.subtitles import SubtitleGenerator
from backend.media.compositor import Compositor
from backend.publishing.publish_manager import PublishingManager, PublishRequest
from backend.orchestrator.recovery import RecoveryManager
from backend.database.session import get_db
from backend.database import crud

class AgentState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"

class PipelineStage(str, Enum):
    IDLE = "IDLE"
    DISCOVER = "DISCOVER"
    RESEARCH = "RESEARCH"
    SCRIPT = "SCRIPT"
    SCENE_PLAN = "SCENE_PLAN"
    RENDER_3D = "RENDER_3D"
    AUDIO_ASSEMBLY = "AUDIO_ASSEMBLY"
    QC = "QC"
    PUBLISH = "PUBLISH"
    COMPLETE = "COMPLETE"

class AutonomousWorker:
    def __init__(
        self,
        db_path: Optional[str] = None,
        storage_dir: str = "output",
        cycle_delay_seconds: int = 10,
        simulated_media: bool = False
    ):
        if db_path is None:
            from backend.config import settings
            db_path = str(settings.base_dir / "data" / "viddy.db")
        self.db_path = db_path
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.cycle_delay_seconds = cycle_delay_seconds
        self.simulated_media = simulated_media
        
        # State machine
        self.state: AgentState = AgentState.STOPPED
        self.current_stage: PipelineStage = PipelineStage.IDLE
        self.progress: float = 0.0
        self.current_action: str = "Studio initialized and standby."
        self.current_video_id: Optional[int] = None
        self.current_job_id: Optional[int] = None
        
        # Agents & Subsystems
        self.discovery_agent = IdeaDiscoveryAgent(db_path=db_path)
        self.research_agent = ResearchAgent()
        self.scriptwriter = ScriptwritingAgent()
        self.visual_director = VisualDirectorAgent()
        self.blender_runner = BlenderRunner()
        self.audio_engine = AudioEngine()
        self.subtitles = SubtitleGenerator()
        self.compositor = Compositor()
        self.qc_agent = QualityControlAgent()
        self.publish_mgr = PublishingManager(db_path=db_path, storage_dir=str(self.storage_dir / "published"))
        self.recovery_mgr = RecoveryManager()
        
        # Async tasks & subscribers
        self._worker_task: Optional[asyncio.Task] = None
        self._subscribers: List[Callable[[Dict[str, Any]], None]] = []

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]):
        """Subscribes an async or sync callback to worker state events."""
        self._subscribers.append(callback)

    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emits an event to registered listeners (e.g. WebSockets) and updates active job in DB."""
        payload = {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state": self.state,
            "stage": self.current_stage,
            "progress": self.progress,
            "current_action": self.current_action,
            "video_id": self.current_video_id,
            "job_id": self.current_job_id,
            **data
        }
        
        # Persist stage progress to SQLite
        if self.db_path and self.current_job_id:
            try:
                with get_db(self.db_path) as session:
                    crud.update_job(
                        session=session,
                        job_id=self.current_job_id,
                        stage=self.current_stage.value,
                        progress=self.progress,
                        current_action=self.current_action
                    )
            except Exception:
                pass
                
        for cb in self._subscribers:
            try:
                res = cb(payload)
                if asyncio.iscoroutine(res):
                    await res
            except Exception:
                pass

    def _log(self, message: str, stage: str = "ORCHESTRATOR", level: str = "INFO"):
        """Logs to SQLite, broadcasts, and prints prominently to terminal standard output."""
        time_str = datetime.now().strftime("%H:%M:%S")
        level_icons = {
            "SUCCESS": "[OK]",
            "INFO": "[*]",
            "WARNING": "[!]",
            "ERROR": "[ERR]"
        }
        icon = level_icons.get(level, "[*]")
        line = f"[{time_str}] {icon} [{stage.upper()}] {message}"
        try:
            print(line, flush=True)
        except (UnicodeEncodeError, Exception):
            try:
                safe_line = line.encode("ascii", errors="replace").decode("ascii")
                print(safe_line, flush=True)
            except Exception:
                pass

        if self.db_path:
            try:
                with get_db(self.db_path) as session:
                    crud.add_log(session, message, stage=stage, level=level)
            except Exception:
                pass

    async def start(self):
        """Starts continuous autonomous operation."""
        if self.state == AgentState.RUNNING:
            return
            
        # Startup recovery
        if self.db_path:
            with get_db(self.db_path) as session:
                self.recovery_mgr.recover_interrupted_jobs(session)
                crud.update_settings(session, running_mode="continuous")
                
        self.state = AgentState.RUNNING
        self._log("Autonomous Video Production Agent started in continuous 24/7 mode.", level="SUCCESS")
        await self._emit_event("AGENT_STARTED", {"message": "Autonomous production loop started."})
        
        self._worker_task = asyncio.create_task(self._continuous_loop())

    async def pause(self):
        """Pauses the continuous worker."""
        self.state = AgentState.PAUSED
        if self.db_path:
            with get_db(self.db_path) as session:
                crud.update_settings(session, running_mode="paused")
        self._log("Autonomous Video Production Agent paused.", level="WARNING")
        await self._emit_event("AGENT_PAUSED", {"message": "Agent suspended. Currently active job will hold."})

    async def resume(self):
        """Resumes paused operations."""
        if self.state == AgentState.RUNNING:
            return
        self.state = AgentState.RUNNING
        if self.db_path:
            with get_db(self.db_path) as session:
                crud.update_settings(session, running_mode="continuous")
        self._log("Autonomous Video Production Agent resumed.", level="SUCCESS")
        await self._emit_event("AGENT_RESUMED", {"message": "Continuous production resumed."})
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._continuous_loop())

    async def stop(self, persist: bool = True):
        """
        Safely terminates autonomous production.
        If persist=False (e.g. server shutdown), keeps the continuous mode in DB so it auto-resumes on next launch.
        """
        self.state = AgentState.STOPPED
        self.current_stage = PipelineStage.IDLE
        self.progress = 0.0
        self.current_action = "Stopped"
        if persist and self.db_path:
            with get_db(self.db_path) as session:
                crud.update_settings(session, running_mode="stopped")
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        self._log("Autonomous Video Production Agent stopped.", level="INFO")
        await self._emit_event("AGENT_STOPPED", {"message": "Agent stopped."})

    async def _continuous_loop(self):
        """
        Infinite autonomous production loop:
        Repeats without waiting for user intervention until paused or stopped.
        """
        while self.state == AgentState.RUNNING:
            try:
                if self.state == AgentState.PAUSED:
                    await asyncio.sleep(1.0)
                    continue
                    
                # Check daily production limits
                if not self._check_daily_limits():
                    self.current_action = "Daily video production limit reached. Waiting for next cycle."
                    self._log(self.current_action, stage="ORCHESTRATOR", level="WARNING")
                    await self._emit_event("LIMIT_REACHED", {"message": self.current_action})
                    await asyncio.sleep(60.0)
                    continue
                    
                # Dynamically retrieve updated delay from settings
                delay = self.cycle_delay_seconds
                if self.db_path:
                    with get_db(self.db_path) as session:
                        st = crud.get_settings(session)
                        if st.cycle_delay_seconds:
                            delay = st.cycle_delay_seconds
                            
                # Run complete production cycle
                await self.run_single_production_cycle()
                
                # Minimum throttle pause between consecutive productions
                if self.state == AgentState.RUNNING:
                    self.current_action = f"Production complete. Starting next discovery cycle in {delay}s..."
                    self.current_stage = PipelineStage.IDLE
                    self.progress = 100.0
                    self._log(f"Cycle completed successfully. Next video production starting in {delay}s...", stage="ORCHESTRATOR", level="SUCCESS")
                    await self._emit_event("CYCLE_COOLDOWN", {"delay": delay})
                    await asyncio.sleep(delay)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log(f"Production cycle exception: {str(e)}", stage="ERROR", level="ERROR")
                if self.db_path and self.current_job_id:
                    with get_db(self.db_path) as session:
                        crud.update_job(session, self.current_job_id, status="failed", details=str(e))
                await self._emit_event("ERROR", {"error": str(e)})
                await asyncio.sleep(5.0)

    def _check_daily_limits(self) -> bool:
        """Verifies configured max daily videos limit."""
        if not self.db_path:
            return True
        with get_db(self.db_path) as session:
            st = crud.get_settings(session)
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if st.last_reset_date != today_str:
                st.daily_videos_produced = 0
                st.last_reset_date = today_str
                session.commit()
            return st.daily_videos_produced < st.max_daily_videos

    async def run_single_production_cycle(self) -> Optional[int]:
        """
        Executes one end-to-end autonomous video production cycle with up to 2 retries on QC failure.
        """
        work_dir = self.storage_dir / f"prod_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        work_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. DISCOVER
        self.current_stage = PipelineStage.DISCOVER
        self.progress = 10.0
        self.current_action = "Discovering original educational concept..."
        self._log("Scanning scientific topics across 8 disciplines for viral concepts...", stage="DISCOVERY", level="INFO")
        
        idea = self.discovery_agent.discover_next_idea()
        self.discovery_agent.record_idea(idea)
        self._log(f"Selected Idea: '{idea.title}' [{idea.category.upper()}] (Curiosity Score: {idea.curiosity_score}/10)", stage="DISCOVERY", level="SUCCESS")
        
        video_id = None
        job_id = None
        if self.db_path:
            with get_db(self.db_path) as session:
                video = crud.create_video(
                    session=session,
                    title=idea.title,
                    topic=idea.category.title(),
                    category=idea.category,
                    script="",
                    hook=idea.hook_angle,
                    status="in_progress"
                )
                video_id = video.id
                job = crud.create_job(session=session, stage="DISCOVER", video_id=video_id)
                job_id = job.id
                self.current_video_id = video_id
                self.current_job_id = job_id

        await self._emit_event("STAGE_CHANGE", {})
                
        # 2. RESEARCH
        self.current_stage = PipelineStage.RESEARCH
        self.progress = 25.0
        self.current_action = f"Researching scientific mechanisms for '{idea.title}'..."
        self._log(f"Researching verified scientific facts and academic sources for '{idea.title}'...", stage="RESEARCH", level="INFO")
        await self._emit_event("STAGE_CHANGE", {"idea": idea.model_dump()})
        concept = self.research_agent.research_topic(idea)
        self._log(f"Research verified: {len(concept.key_facts)} core facts extracted with sources: {', '.join(concept.scientific_sources[:2])}", stage="RESEARCH", level="SUCCESS")
        
        # 3. SCRIPT
        self.current_stage = PipelineStage.SCRIPT
        self.progress = 40.0
        self.current_action = "Writing viral narration script & platform metadata..."
        self._log("Writing 30-45s retention-optimized script and viral TikTok commentary...", stage="SCRIPT", level="INFO")
        await self._emit_event("STAGE_CHANGE", {})
        script = self.scriptwriter.generate_script(concept)
        
        self._log(f"Script generated! Estimated runtime: {script.estimated_duration:.0f}s", stage="SCRIPT", level="SUCCESS")
        self._log(f"TikTok Pinned Commentary: {script.tiktok_commentary}", stage="SCRIPT", level="INFO")
        self._log(f"TikTok Viral Hashtags: {script.tiktok_hashtags[:75]}...", stage="SCRIPT", level="INFO")
        
        if self.db_path and video_id:
            with get_db(self.db_path) as session:
                crud.update_video(
                    session,
                    video_id,
                    script=script.full_narration,
                    hook=script.hook,
                    tiktok_commentary=script.tiktok_commentary,
                    tiktok_hashtags=script.tiktok_hashtags,
                    youtube_tags=",".join(script.youtube_tags)
                )
                
        # 4-7. AUDIO, 3D RENDER, ASSEMBLE & QC (WITH AUTOMATED RETRY UP TO 2 TIMES)
        max_attempts = 2
        for attempt in range(1, max_attempts + 1):
            # 4. AUDIO SYNTHESIS & CADENCE
            self.current_stage = PipelineStage.AUDIO_ASSEMBLY
            self.progress = 55.0
            self.current_action = f"Synthesizing voice narration and measuring cadence (Attempt {attempt}/{max_attempts})..."
            self._log("Synthesizing neural voiceover via Edge-TTS and generating kinetic subtitles...", stage="AUDIO", level="INFO")
            await self._emit_event("STAGE_CHANGE", {"attempt": attempt})
            
            narration_path = str(work_dir / f"final_audio_att{attempt}.mp3")
            if self.simulated_media:
                Path(narration_path).write_bytes(b"dummy audio")
                actual_duration = 30.0
            else:
                voice = "en-US-ChristopherNeural"
                if self.db_path:
                    with get_db(self.db_path) as session:
                        st = crud.get_settings(session)
                        voice = st.default_voice or voice
                        
                narration_path, actual_duration = await self.audio_engine.synthesize_speech(
                    text=script.full_narration,
                    output_path=narration_path,
                    voice=voice
                )
                
            self._log(f"Neural audio voiceover ready ({actual_duration:.1f}s). Generating styled kinetic subtitles...", stage="AUDIO", level="SUCCESS")

            # Subtitles
            subtitles_path = str(work_dir / f"subtitles_att{attempt}.ass")
            if self.simulated_media:
                Path(subtitles_path).write_text("dummy subtitles")
            else:
                self.subtitles.generate_ass_subtitles(
                    script_blocks=script.narration_blocks,
                    total_duration=actual_duration,
                    output_ass_path=subtitles_path
                )

            # 5. TITLED 3D VIDEO GENERATION (NATIVE PYTHON + FFMPEG, NO BLENDER)
            self.current_stage = PipelineStage.RENDER_3D
            self.progress = 70.0
            self.current_action = f"Rendering 1080x1920 30FPS 3D animation ({actual_duration:.1f}s, Attempt {attempt}/{max_attempts})..."
            self._log(f"Rendering native 3D animation for '{concept.category}' matching {actual_duration:.1f}s...", stage="3D RENDER", level="INFO")
            await self._emit_event("STAGE_CHANGE", {"attempt": attempt})
            
            titled_video_path = str(work_dir / f"titled_3d_att{attempt}.mp4")
            if self.simulated_media:
                Path(titled_video_path).write_bytes(b"dummy clip data 1080x1920")
            else:
                await self.blender_runner.generate_titled_video_async(
                    category=concept.category,
                    title=script.title,
                    duration=actual_duration,
                    output_video_path=titled_video_path,
                    timeout_seconds=240.0
                )
            self._log("Native 3D animation rendered successfully.", stage="3D RENDER", level="SUCCESS")

            # 6. MASTER SHORT ASSEMBLY
            self.progress = 85.0
            self.current_action = "Combining titled_3d.mp4 and final_audio.mp3 into final_short.mp4..."
            self._log("FFmpeg Compositor: Combining titled_3d.mp4 and final_audio.mp3 with vertical kinetic subtitles...", stage="COMPOSITE", level="INFO")
            final_video_path = str(work_dir / "final_short.mp4")
            thumbnail_path = str(work_dir / "thumbnail.jpg")
            
            if self.simulated_media:
                Path(final_video_path).write_bytes(b"dummy final video")
                Path(thumbnail_path).write_bytes(b"dummy thumb")
            else:
                await self.compositor.assemble_video_async(
                    video_clips=[titled_video_path],
                    narration_path=narration_path,
                    subtitles_path=subtitles_path,
                    output_path=final_video_path,
                    target_duration=actual_duration,
                    thumbnail_output_path=thumbnail_path,
                    timeout_seconds=180.0
                )

            # 7. QUALITY CONTROL
            self.current_stage = PipelineStage.QC
            self.progress = 92.0
            self.current_action = "Performing automated quality control validation..."
            self._log("Running automated Quality Control inspection (FFprobe resolution, audio sync, frame rates)...", stage="QC", level="INFO")
            await self._emit_event("STAGE_CHANGE", {})
            
            qc_report = self.qc_agent.validate_video(final_video_path)
            if self.simulated_media:
                qc_report = QCReport(passed=True, duration=actual_duration, width=1080, height=1920, has_audio=True)
                
            if qc_report.passed:
                self._log(f"QC Passed! Duration: {qc_report.duration:.1f}s, Resolution: {qc_report.width}x{qc_report.height} @ 30fps", stage="QC", level="SUCCESS")
                break
            else:
                self._log(f"Attempt {attempt} QC failed: {', '.join(qc_report.issues)}", stage="QC", level="WARNING")
                if self.db_path and video_id:
                    with get_db(self.db_path) as session:
                        v = crud.get_video_by_id(session, video_id)
                        if v:
                            v.retry_count = attempt
                            session.commit()
                if attempt == max_attempts:
                    self._log(f"Video '{idea.title}' failed all {max_attempts} QC attempts. Quarantining.", stage="QC", level="ERROR")
                    if self.db_path and video_id:
                        with get_db(self.db_path) as session:
                            crud.update_video(session, video_id, status="failed", qc_details=", ".join(qc_report.issues))
                            if job_id:
                                crud.update_job(session, job_id, status="failed", details=", ".join(qc_report.issues))
                    return None
                await asyncio.sleep(2.0)

        # 8. PUBLISHING
        self.current_stage = PipelineStage.PUBLISH
        self.progress = 95.0
        self.current_action = "Publishing to configured destinations..."
        await self._emit_event("STAGE_CHANGE", {})
        
        destinations = ["local"]
        if self.db_path:
            with get_db(self.db_path) as session:
                st = crud.get_settings(session)
                destinations = self.publish_mgr.resolve_destinations(st.publish_destination)
                
        self._log(f"Publishing video to destinations: {destinations}...", stage="PUBLISH", level="INFO")
        
        pub_req = PublishRequest(
            video_path=final_video_path,
            title=script.title,
            description=script.youtube_description,
            tags=script.youtube_tags,
            tiktok_caption=script.tiktok_caption,
            tiktok_hashtags=script.tiktok_hashtags,
            tiktok_commentary=script.tiktok_commentary,
            thumbnail_path=thumbnail_path,
            destinations=destinations
        )
        pub_results = await self.publish_mgr.publish(pub_req)
        
        # 9. COMPLETE & RECORD
        self.current_stage = PipelineStage.COMPLETE
        self.progress = 100.0
        self.current_action = "Production finished and recorded in video library."
        
        yt_link = next((r.url for r in pub_results if r.platform == "youtube" and r.success), None)
        tt_link = next((r.url for r in pub_results if r.platform == "tiktok" and r.success), None)
        local_link = next((r.url for r in pub_results if r.platform == "local" and r.success), None)
        
        if self.db_path and video_id:
            with get_db(self.db_path) as session:
                crud.update_video(
                    session=session,
                    video_id=video_id,
                    duration=actual_duration,
                    status="completed",
                    video_path=local_link or final_video_path,
                    thumbnail_path=thumbnail_path,
                    subtitle_path=subtitles_path,
                    published_destinations=",".join([r.platform for r in pub_results if r.success]),
                    youtube_url=yt_link,
                    tiktok_url=tt_link,
                    tiktok_commentary=script.tiktok_commentary,
                    tiktok_hashtags=script.tiktok_hashtags,
                    youtube_tags=",".join(script.youtube_tags),
                    qc_passed=True
                )
                if job_id:
                    crud.update_job(session, job_id, status="completed", progress=100.0)
                st = crud.get_settings(session)
                st.daily_videos_produced += 1
                session.commit()
                
        successful_destinations = [r.platform for r in pub_results if r.success]
        self._log(f"Autonomous production published successfully to: {successful_destinations}", stage="PUBLISH", level="SUCCESS")
        if tt_link or "tiktok" in successful_destinations:
            self._log(f"TikTok commentary ready to pin: {script.tiktok_commentary}", stage="PUBLISH", level="SUCCESS")
        await self._emit_event("VIDEO_COMPLETED", {"video_id": video_id, "title": idea.title, "published": [r.model_dump(mode='json') for r in pub_results]})
        
        return video_id
