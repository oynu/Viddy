import os
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List

from backend.orchestrator.state_machine import AgentState, PipelineStage
from backend.orchestrator.recovery import RecoveryManager
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
from backend.database.session import get_db
from backend.database import crud
from backend.database.models import SettingModel

class AutonomousWorker:
    """
    Continuous Background Production Engine.
    Operates in an infinite autonomous loop:
    Discover -> Research -> Script -> 3D Scene -> Render -> Assemble -> QC -> Publish -> Loop
    """
    def __init__(
        self,
        db_path: Optional[str] = None,
        storage_dir: str = "output",
        simulated_media: bool = False,
        cycle_delay_seconds: float = 5.0
    ):
        self.db_path = db_path
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.simulated_media = simulated_media
        self.cycle_delay_seconds = cycle_delay_seconds
        
        self.state = AgentState.STOPPED
        self.current_stage = PipelineStage.IDLE
        self.current_job_id: Optional[int] = None
        self.current_video_id: Optional[int] = None
        self.current_action: str = "Ready"
        self.progress: float = 0.0
        
        # Sub-agents
        self.discovery_agent = IdeaDiscoveryAgent(db_path=db_path)
        self.research_agent = ResearchAgent()
        self.scriptwriter = ScriptwritingAgent()
        self.visual_director = VisualDirectorAgent()
        self.blender_runner = BlenderRunner()
        self.audio_engine = AudioEngine()
        self.subtitle_gen = SubtitleGenerator()
        self.compositor = Compositor()
        self.qc_agent = QualityControlAgent()
        self.publish_mgr = PublishingManager(db_path=db_path, storage_dir=str(self.storage_dir / "published"))
        self.recovery_mgr = RecoveryManager(db_path=db_path, storage_dir=str(self.storage_dir))
        
        self._worker_task: Optional[asyncio.Task] = None
        self._subscribers: List[Callable[[Dict[str, Any]], Any]] = []

    def subscribe(self, callback: Callable[[Dict[str, Any]], Any]):
        """Registers a callback for real-time progress events."""
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
        if self.db_path:
            with get_db(self.db_path) as session:
                crud.add_log(session, message, stage=stage, level=level)

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
        self._log("Autonomous Video Production Agent started.", level="SUCCESS")
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

    async def stop(self):
        """Safely terminates autonomous production."""
        self.state = AgentState.STOPPED
        self.current_stage = PipelineStage.IDLE
        self.progress = 0.0
        self.current_action = "Stopped"
        if self.db_path:
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
        
        idea = self.discovery_agent.discover_next_idea()
        self.discovery_agent.record_idea(idea)
        self._log(f"Discovered idea: '{idea.title}' ({idea.category})", stage="DISCOVERY", level="SUCCESS")
        
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
        await self._emit_event("STAGE_CHANGE", {"idea": idea.model_dump()})
        concept = self.research_agent.research_topic(idea)
        
        # 3. SCRIPT
        self.current_stage = PipelineStage.SCRIPT
        self.progress = 40.0
        self.current_action = "Writing viral narration script & platform metadata..."
        await self._emit_event("STAGE_CHANGE", {})
        script = self.scriptwriter.generate_script(concept)
        
        if self.db_path and video_id:
            with get_db(self.db_path) as session:
                crud.update_video(session, video_id, script=script.full_narration, hook=script.hook)
                
        # 4. SCENE_PLAN
        self.current_stage = PipelineStage.SCENE_PLAN
        self.progress = 50.0
        self.current_action = "Generating 3D low-poly scene breakdown & camera choreography..."
        await self._emit_event("STAGE_CHANGE", {})
        plan = self.visual_director.create_production_plan(concept, script)
        
        # 5-7. RENDER, ASSEMBLE & QC (WITH AUTOMATED RETRY UP TO 2 TIMES)
        max_attempts = 2
        for attempt in range(1, max_attempts + 1):
            # 5. RENDER_3D
            self.current_stage = PipelineStage.RENDER_3D
            self.progress = 65.0
            self.current_action = f"Rendering {len(plan.scenes)} low-poly 3D scenes (Attempt {attempt}/{max_attempts})..."
            await self._emit_event("STAGE_CHANGE", {"attempt": attempt})
            
            rendered_clips = []
            if self.simulated_media:
                mock_clip = work_dir / f"scene_1_att{attempt}.mp4"
                mock_clip.write_bytes(b"dummy clip data 1080x1920")
                rendered_clips.append(str(mock_clip))
            else:
                for s_idx, scene in enumerate(plan.scenes):
                    clip_path = await self.blender_runner.render_scene_async(
                        scene=scene,
                        output_dir=str(work_dir / f"scene_{scene.scene_id}"),
                        output_video_name=f"scene_{scene.scene_id}.mp4",
                        timeout_seconds=120.0
                    )
                    rendered_clips.append(clip_path)
                    self.progress = 65.0 + ((s_idx + 1) / len(plan.scenes)) * 10.0
                    await self._emit_event("RENDER_PROGRESS", {"scene_index": s_idx + 1, "total_scenes": len(plan.scenes)})

            # 6. AUDIO & ASSEMBLY
            self.current_stage = PipelineStage.AUDIO_ASSEMBLY
            self.progress = 80.0
            self.current_action = "Synthesizing voice narration, ASS vertical subtitles & audio muxing..."
            await self._emit_event("STAGE_CHANGE", {})
            
            narration_path = str(work_dir / f"narration_att{attempt}.mp3")
            subtitles_path = str(work_dir / f"subtitles_att{attempt}.ass")
            final_video_path = str(work_dir / f"final_video_att{attempt}.mp4")
            thumbnail_path = str(work_dir / f"thumbnail_att{attempt}.jpg")
            
            if self.simulated_media:
                Path(narration_path).write_bytes(b"dummy mp3 data")
                Path(subtitles_path).write_text("[Script Info]\nPlayResY: 1920\n", encoding="utf-8")
                Path(final_video_path).write_bytes(b"dummy full video data")
                Path(thumbnail_path).write_bytes(b"dummy jpg data")
                actual_duration = script.estimated_duration
            else:
                voice_path, actual_duration = await self.audio_engine.generate_voiceover(
                    text=script.full_narration,
                    output_path=narration_path
                )
                self.subtitle_gen.generate_styled_ass(
                    text=script.full_narration,
                    total_duration=actual_duration,
                    output_path=subtitles_path
                )
                bgm_path = self.audio_engine.generate_ambient_bgm(
                    output_path=str(work_dir / f"ambient_bgm_att{attempt}.wav"),
                    duration=actual_duration
                )
                await self.compositor.assemble_video_async(
                    video_clips=rendered_clips,
                    narration_path=voice_path,
                    bgm_path=bgm_path,
                    subtitles_path=subtitles_path,
                    output_path=final_video_path
                )
                self.compositor.extract_thumbnail(final_video_path, thumbnail_path)

            # 7. QUALITY CONTROL
            self.current_stage = PipelineStage.QC
            self.progress = 90.0
            self.current_action = "Running automated quality control inspection..."
            await self._emit_event("STAGE_CHANGE", {})
            
            qc_report = self.qc_agent.validate_video(final_video_path)
            if self.simulated_media:
                qc_report = QCReport(passed=True, duration=actual_duration, width=1080, height=1920, has_audio=True)
                
            if qc_report.passed:
                self._log(f"QC Passed successfully! Duration: {qc_report.duration:.1f}s", stage="QC", level="SUCCESS")
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
                
        pub_req = PublishRequest(
            video_path=final_video_path,
            title=script.title,
            description=script.youtube_description,
            tags=script.youtube_tags,
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
                    qc_passed=True
                )
                if job_id:
                    crud.update_job(session, job_id, status="completed", progress=100.0)
                st = crud.get_settings(session)
                st.daily_videos_produced += 1
                session.commit()
                
        self._log(f"Successfully published '{idea.title}' to: {[r.platform for r in pub_results if r.success]}", stage="PUBLISH", level="SUCCESS")
        await self._emit_event("VIDEO_COMPLETED", {"video_id": video_id, "title": idea.title, "published": [r.model_dump(mode='json') for r in pub_results]})
        
        return video_id
