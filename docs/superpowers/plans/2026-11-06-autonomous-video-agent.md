# Autonomous AI Video Production & Publishing Agent (Viddy) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fully autonomous, continuous 24/7 AI video production and publishing agent that discovers educational concepts, writes scripts, generates low-poly 3D animations in Blender via Python, quality-checks the output, publishes to YouTube Shorts and TikTok, and immediately starts the next video without waiting for user approval.

**Architecture:** A persistent background worker orchestrator driven by FastAPI and SQLite coordinates modular AI agents (Discovery, Research, Script, Visual Director, Quality Control, and Publishing). Media production uses headless Blender Python scripts for procedural low-poly 3D vertical rendering, Edge-TTS/audio engines for voiceover, and FFmpeg for composition, complemented by a real-time reactive React dashboard.

**Tech Stack:** Python 3.11+/3.14+, FastAPI, SQLAlchemy, SQLite, Pydantic, Blender (Python `bpy`), FFmpeg, Edge-TTS, Google YouTube Data API v3, TikTok Content Posting API v2, React 19, TypeScript, Vite, Tailwind CSS, Lucide React.

**Spec:** `docs/superpowers/specs/2026-11-06-autonomous-video-agent-design.md`

## Global Constraints
- Target output must be 9:16 vertical video at 1080x1920, 30 FPS, H.264 MP4 with AAC audio.
- Continuous loop must never halt permanently on failure: record error, retry intelligently, and continue to next production.
- Production preferences (destinations, limits, voice, duration) must persist in SQLite database across restarts.
- Publishing must support YouTube Shorts, TikTok, both, or local archive mode without fake mock progress bars.
- Zero manual approval required in autonomous mode: agent immediately kicks off the next video upon publishing or archiving.

## Review Focus
1. **Uninterrupted Continuous Loop**: If a video fails during rendering or QC, the worker logs the error, attempts up to 2 retries, and transitions seamlessly to the next idea rather than freezing the loop.
2. **Restart Recovery**: If the application or server crashes mid-render, on startup the worker detects in-flight jobs, cleans up temp files, marks the job as recovered/re-queued, and resumes continuous operation.
3. **Blender Headless Reliability**: Low-poly 3D generation must use validated Python scripts that run cleanly in headless mode (`blender -b -P`) with zero GUI popups or modal locks.
4. **Platform Publishing Authentication**: Secure token refresh logic for YouTube and TikTok prevents broken uploads due to expired access tokens during continuous multi-hour runs.
5. **Rate Limiting & Cost Guardrails**: Configurable daily video caps and backoff timers prevent runaway API spending or platform throttling.

---

### Task 1: System Environment & Infrastructure Setup

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/config.py`
- Create: `backend/database/models.py`
- Create: `backend/database/session.py`
- Create: `backend/database/crud.py`
- Test: `backend/tests/test_database.py`

**Interfaces:**
- Consumes: Nothing
- Produces: SQLite tables (`videos`, `jobs`, `ideas`, `settings`, `logs`, `channels`), configuration models `Settings`, and database session helper `get_db()`.

- [ ] **Step 1: Write the failing test for database models and settings**

```python
# backend/tests/test_database.py
import pytest
from backend.database.session import init_db, get_db
from backend.database import crud
from backend.database.models import SettingModel, VideoModel, JobModel

def test_database_initialization_and_crud(tmp_path):
    db_file = tmp_path / "test_viddy.db"
    init_db(str(db_file))
    
    with get_db(str(db_file)) as session:
        # Check default settings are created
        settings = crud.get_settings(session)
        assert settings.running_mode == "continuous"
        assert settings.publish_destination in ["local", "both", "youtube", "tiktok"]
        
        # Test creating and fetching video
        video = crud.create_video(
            session,
            title="What if the Moon vanished?",
            topic="Astrophysics",
            script="Imagine looking up at the night sky...",
            duration=35.0,
            status="completed"
        )
        assert video.id is not None
        fetched = crud.get_video_by_id(session, video.id)
        assert fetched.title == "What if the Moon vanished?"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_database.py -v`
Expected: FAIL with "No module named backend"

- [ ] **Step 3: Implement database models, session, and CRUD in `backend/database/`**

Create `backend/requirements.txt`, `backend/config.py`, `backend/database/models.py`, `backend/database/session.py`, and `backend/database/crud.py` with SQLAlchemy models for `Video`, `Job`, `IdeaHistory`, `SystemSetting`, and `PublishAccount`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_database.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat(infra): setup database models, config, and test suite"
```

---

### Task 2: Autonomous Idea Discovery & Research Agent

**Files:**
- Create: `backend/agents/idea_discovery.py`
- Create: `backend/agents/researcher.py`
- Test: `backend/tests/test_idea_discovery.py`

**Interfaces:**
- Consumes: `backend.database.crud` for duplicate checking and history recording.
- Produces: `IdeaDiscoveryAgent.discover_next_idea() -> IdeaProposal`, `ResearchAgent.research_topic(idea: IdeaProposal) -> ResearchedConcept`.

- [ ] **Step 1: Write the failing test for Idea Discovery & Researcher**

```python
# backend/tests/test_idea_discovery.py
from backend.agents.idea_discovery import IdeaDiscoveryAgent, IdeaProposal
from backend.agents.researcher import ResearchAgent, ResearchedConcept
from backend.database.session import init_db, get_db

def test_idea_discovery_uniqueness(tmp_path):
    db_file = tmp_path / "test_ideas.db"
    init_db(str(db_file))
    
    agent = IdeaDiscoveryAgent(db_path=str(db_file))
    idea1 = agent.discover_next_idea()
    assert isinstance(idea1, IdeaProposal)
    assert len(idea1.title) > 5
    assert idea1.category in ["astronomy", "physics", "biology", "chemistry", "technology", "everyday_science"]
    assert idea1.curiosity_score >= 7.0
    
    # Save idea to history and verify duplicate avoidance
    agent.record_idea(idea1)
    idea2 = agent.discover_next_idea()
    assert idea2.title != idea1.title

def test_research_agent():
    researcher = ResearchAgent()
    idea = IdeaProposal(
        title="What if Earth's Gravity Doubled?",
        category="physics",
        hook_angle="Human bodies crushed under their own weight",
        curiosity_score=9.2
    )
    result = researcher.research_topic(idea)
    assert isinstance(result, ResearchedConcept)
    assert len(result.key_facts) >= 3
    assert len(result.scientific_sources) >= 1
    assert "blood pressure" in " ".join(result.key_facts).lower() or "gravity" in " ".join(result.key_facts).lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_idea_discovery.py -v`
Expected: FAIL with "No module named backend.agents.idea_discovery"

- [ ] **Step 3: Implement `IdeaDiscoveryAgent` and `ResearchAgent`**

Include a comprehensive built-in catalog of 8 scientific domains with "What if...?" and "How does...?" algorithmic concept generators, AI LLM enhancement hooks (Gemini/OpenAI), internal scoring metrics, and anti-duplication memory checking past titles.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_idea_discovery.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/agents/idea_discovery.py backend/agents/researcher.py backend/tests/test_idea_discovery.py
git commit -m "feat(agents): implement idea discovery and research agents"
```

---

### Task 3: Scriptwriting & Visual Director Agent

**Files:**
- Create: `backend/agents/scriptwriter.py`
- Create: `backend/agents/visual_director.py`
- Test: `backend/tests/test_scriptwriter.py`

**Interfaces:**
- Consumes: `ResearchedConcept` from `ResearchAgent`.
- Produces: `VideoScript` (hook, narration lines, pacing, word timings) and `VisualProductionPlan` (scene list, 3D low-poly scene types, camera motions, lighting setups).

- [ ] **Step 1: Write the failing test for Scriptwriting & Visual Director**

```python
# backend/tests/test_scriptwriter.py
from backend.agents.idea_discovery import IdeaProposal
from backend.agents.researcher import ResearchedConcept
from backend.agents.scriptwriter import ScriptwritingAgent, VideoScript
from backend.agents.visual_director import VisualDirectorAgent, VisualProductionPlan

def test_script_generation():
    concept = ResearchedConcept(
        title="What if the Moon Disappeared?",
        category="astronomy",
        key_facts=["Tides would shrink by 70%", "Earth axis would wobble wildly", "Nights would be pitch black"],
        scientific_sources=["NASA Solar System Exploration"],
        target_duration=45.0
    )
    
    scriptwriter = ScriptwritingAgent()
    script = scriptwriter.generate_script(concept)
    assert isinstance(script, VideoScript)
    assert len(script.hook) > 10
    assert len(script.narration_blocks) >= 3
    assert 20.0 <= script.estimated_duration <= 60.0
    assert len(script.call_to_action) > 0

def test_visual_director_plan():
    director = VisualDirectorAgent()
    concept = ResearchedConcept(
        title="What if the Moon Disappeared?",
        category="astronomy",
        key_facts=["Tides shrink", "Earth wobbles"],
        scientific_sources=["NASA"],
        target_duration=40.0
    )
    script = VideoScript(
        title="What if the Moon Disappeared?",
        hook="What if tonight, you looked up... and the Moon was just GONE?",
        narration_blocks=["First, ocean tides would collapse by over 70 percent.", "Next, Earth's stable 23-degree tilt would destabilize."],
        estimated_duration=35.0,
        call_to_action="Subscribe to Viddy for daily science mysteries!"
    )
    plan = director.create_production_plan(concept, script)
    assert isinstance(plan, VisualProductionPlan)
    assert len(plan.scenes) >= 2
    assert plan.scenes[0].generator_type in ["space", "physics", "micro", "tech", "atmosphere"]
    assert plan.scenes[0].camera_motion in ["orbit", "flythrough", "zoom_in", "pan", "top_down"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_scriptwriter.py -v`
Expected: FAIL with "No module named backend.agents.scriptwriter"

- [ ] **Step 3: Implement `ScriptwritingAgent` and `VisualDirectorAgent`**

Implement narrative structuring (Hook -> Escalation -> Mechanism -> Mind-bending conclusion -> CTA), timing calculations (130-150 words per minute), and visual mapping to low-poly 3D scene templates.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_scriptwriter.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/agents/scriptwriter.py backend/agents/visual_director.py backend/tests/test_scriptwriter.py
git commit -m "feat(agents): implement scriptwriting and visual director agents"
```

---

### Task 4: Voice Synthesis, Subtitles & Audio Engine

**Files:**
- Create: `backend/media/audio_engine.py`
- Create: `backend/media/subtitles.py`
- Test: `backend/tests/test_audio_engine.py`

**Interfaces:**
- Consumes: `VideoScript` text.
- Produces: Final narration audio file (`.wav` or `.mp3`), timing word alignment, synchronized vertical subtitle file (`.ass` / `.srt`), and background music mix.

- [ ] **Step 1: Write the failing test for Audio & Subtitles**

```python
# backend/tests/test_audio_engine.py
import pytest
import os
from backend.media.audio_engine import AudioEngine
from backend.media.subtitles import SubtitleGenerator

@pytest.mark.asyncio
async def test_audio_synthesis_and_subtitles(tmp_path):
    output_audio = tmp_path / "test_narration.mp3"
    output_subtitles = tmp_path / "test_subs.ass"
    
    engine = AudioEngine()
    test_text = "What if gravity vanished for just five seconds? Everything not bolted down would launch into the sky."
    
    audio_path, duration = await engine.generate_voiceover(test_text, str(output_audio))
    assert os.path.exists(audio_path)
    assert duration > 1.0
    
    sub_gen = SubtitleGenerator()
    sub_path = sub_gen.generate_styled_ass(test_text, duration, str(output_subtitles))
    assert os.path.exists(sub_path)
    with open(sub_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "[Script Info]" in content
        assert "Style: Default" in content
        assert "gravity vanished" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_audio_engine.py -v`
Expected: FAIL with "No module named backend.media.audio_engine"

- [ ] **Step 3: Implement `AudioEngine` and `SubtitleGenerator`**

Implement Edge-TTS asynchronous generator with local fallback, duration extraction, procedural ambient synth background music generator/mixer, and `.ass` styled subtitle creator featuring high-contrast vertical formatting.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_audio_engine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/media/audio_engine.py backend/media/subtitles.py backend/tests/test_audio_engine.py
git commit -m "feat(media): implement voice synthesis, audio mixing, and vertical subtitles"
```

---

### Task 5: Programmatic Blender Low-Poly 3D Engine

**Files:**
- Create: `backend/blender/runner.py`
- Create: `backend/blender/scripts/base_scene.py`
- Create: `backend/blender/scripts/space_scene.py`
- Create: `backend/blender/scripts/physics_scene.py`
- Create: `backend/blender/scripts/micro_scene.py`
- Create: `backend/blender/scripts/tech_scene.py`
- Create: `backend/blender/scripts/render_orchestrator.py`
- Test: `backend/tests/test_blender_engine.py`

**Interfaces:**
- Consumes: `VisualProductionPlan` from `VisualDirectorAgent`.
- Produces: Rendered vertical 9:16 video segment or image sequence (`1080x1920 @ 30fps`).

- [ ] **Step 1: Write the failing test for Blender Generator Scripts**

```python
# backend/tests/test_blender_engine.py
import os
from backend.blender.runner import BlenderRunner
from backend.agents.visual_director import SceneInstruction

def test_blender_script_generation(tmp_path):
    runner = BlenderRunner()
    scene = SceneInstruction(
        scene_id=1,
        generator_type="space",
        duration=4.0,
        camera_motion="orbit",
        description="Low poly Earth with vanishing Moon in deep space"
    )
    script_path = runner.generate_blender_script(scene, output_dir=str(tmp_path))
    assert os.path.exists(script_path)
    with open(script_path, "r", encoding="utf-8") as f:
        code = f.read()
        assert "import bpy" in code
        assert "bpy.context.scene.render.resolution_x = 1080" in code
        assert "bpy.context.scene.render.resolution_y = 1920" in code
        assert "bpy.context.scene.render.fps = 30" in code
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_blender_engine.py -v`
Expected: FAIL with "No module named backend.blender.runner"

- [ ] **Step 3: Implement Blender runner and procedural low-poly scene generators**

Build modular scene templates with:
- Premium low-poly aesthetic (flat shading, geometric bevels, vibrant pastel/neon palettes).
- Cinematic 3-point lighting (key, fill, rim) + emission shaders.
- Dynamic camera rig (9:16 vertical sensor, focal length 35mm, Bezier curves for smooth panning/zooming/orbiting).
- Headless execution harness (`blender -b -P script.py`) with software fallbacks if GPU is busy.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_blender_engine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/blender/ backend/tests/test_blender_engine.py
git commit -m "feat(blender): implement programmatic low-poly 3D generator and headless runner"
```

---

### Task 6: Video Assembly & Quality Control (QC) Agent

**Files:**
- Create: `backend/media/compositor.py`
- Create: `backend/agents/quality_control.py`
- Test: `backend/tests/test_quality_control.py`

**Interfaces:**
- Consumes: Rendered 3D video clips, audio narration, background music, subtitle file.
- Produces: Assembled 1080x1920 MP4 video, and `QCReport(passed: bool, duration: float, issues: List[str])`.

- [ ] **Step 1: Write the failing test for Compositor & QC Agent**

```python
# backend/tests/test_quality_control.py
import pytest
from backend.agents.quality_control import QualityControlAgent, QCReport

def test_qc_validation_rules(tmp_path):
    qc = QualityControlAgent()
    
    # Non-existent file must fail QC
    report = qc.validate_video(str(tmp_path / "non_existent.mp4"))
    assert not report.passed
    assert "File not found" in report.issues[0]

    # Test parameter validation rules
    valid_probe = {
        "format": {"duration": "35.2", "size": "15000000"},
        "streams": [
            {"codec_type": "video", "width": 1080, "height": 1920, "r_frame_rate": "30/1"},
            {"codec_type": "audio", "codec_name": "aac", "channels": 2}
        ]
    }
    report_valid = qc.evaluate_probe_data(valid_probe)
    assert report_valid.passed
    assert len(report_valid.issues) == 0

    # Wrong resolution must fail
    invalid_probe = {
        "format": {"duration": "35.2", "size": "15000000"},
        "streams": [
            {"codec_type": "video", "width": 720, "height": 1280, "r_frame_rate": "30/1"},
            {"codec_type": "audio", "codec_name": "aac", "channels": 2}
        ]
    }
    report_invalid = qc.evaluate_probe_data(invalid_probe)
    assert not report_invalid.passed
    assert any("resolution" in i.lower() for i in report_invalid.issues)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_quality_control.py -v`
Expected: FAIL with "No module named backend.agents.quality_control"

- [ ] **Step 3: Implement `Compositor` and `QualityControlAgent`**

Use FFmpeg to stitch scenes, burn ASS subtitles with crisp outlines, mix audio levels, and encode H.264/AAC. Implement QC checks: resolution, frame rate, duration bounds, audio stream validation, and frame blanking detection.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_quality_control.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/media/compositor.py backend/agents/quality_control.py backend/tests/test_quality_control.py
git commit -m "feat(qc): implement FFmpeg compositor and multi-stage quality control agent"
```

---

### Task 7: Autonomous Social Media Publishing Engine

**Files:**
- Create: `backend/publishing/youtube_publisher.py`
- Create: `backend/publishing/tiktok_publisher.py`
- Create: `backend/publishing/local_publisher.py`
- Create: `backend/publishing/publish_manager.py`
- Test: `backend/tests/test_publishing.py`

**Interfaces:**
- Consumes: Final QC-passed video file and video metadata (title, description, tags).
- Produces: `PublishResult(success: bool, platform: str, url: str, published_at: datetime)`.

- [ ] **Step 1: Write the failing test for Publishing Manager**

```python
# backend/tests/test_publishing.py
import pytest
from backend.publishing.publish_manager import PublishingManager, PublishRequest, PublishResult
from backend.database.session import init_db, get_db

@pytest.mark.asyncio
async def test_local_publishing(tmp_path):
    db_file = tmp_path / "test_pub.db"
    init_db(str(db_file))
    
    # Create dummy video file
    dummy_video = tmp_path / "test_video.mp4"
    dummy_video.write_bytes(b"dummy video data")
    
    manager = PublishingManager(db_path=str(db_file), storage_dir=str(tmp_path / "published"))
    req = PublishRequest(
        video_path=str(dummy_video),
        title="What if Gravity Inverted?",
        description="A journey into inverted physics. #science #physics #shorts",
        tags=["science", "physics", "shorts"],
        destinations=["local"]
    )
    
    results = await manager.publish(req)
    assert len(results) == 1
    assert results[0].platform == "local"
    assert results[0].success is True
    assert (tmp_path / "published").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_publishing.py -v`
Expected: FAIL with "No module named backend.publishing.publish_manager"

- [ ] **Step 3: Implement YouTube Shorts, TikTok, and Local Storage publishers**

Implement OAuth2 flow handlers, token refresh routines, YouTube resumable chunked upload API, TikTok Content Posting API v2, and Local Archive organizer with `metadata.json`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_publishing.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/publishing/ backend/tests/test_publishing.py
git commit -m "feat(publishing): implement YouTube Shorts, TikTok, and Local publishing manager"
```

---

### Task 8: Continuous Orchestration Engine & Background Worker

**Files:**
- Create: `backend/orchestrator/state_machine.py`
- Create: `backend/orchestrator/worker.py`
- Create: `backend/orchestrator/recovery.py`
- Test: `backend/tests/test_orchestrator.py`

**Interfaces:**
- Consumes: All agents (Discovery, Research, Script, Visual, Blender, Compositor, QC, Publishing).
- Produces: Autonomous infinite loop with `start()`, `pause()`, `resume()`, `stop()` methods, persisting status to SQLite.

- [ ] **Step 1: Write the failing test for Continuous Orchestration Worker**

```python
# backend/tests/test_orchestrator.py
import pytest
import asyncio
from backend.orchestrator.worker import AutonomousWorker
from backend.database.session import init_db, get_db
from backend.database import crud

@pytest.mark.asyncio
async def test_worker_lifecycle_controls(tmp_path):
    db_file = tmp_path / "test_orch.db"
    init_db(str(db_file))
    
    worker = AutonomousWorker(db_path=str(db_file), simulated_media=True)
    assert worker.state == "STOPPED"
    
    # Start the continuous agent
    await worker.start()
    assert worker.state == "RUNNING"
    
    # Pause the continuous agent
    await worker.pause()
    assert worker.state == "PAUSED"
    
    # Resume the continuous agent
    await worker.resume()
    assert worker.state == "RUNNING"
    
    # Stop the continuous agent
    await worker.stop()
    assert worker.state == "STOPPED"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_orchestrator.py -v`
Expected: FAIL with "No module named backend.orchestrator.worker"

- [ ] **Step 3: Implement `AutonomousWorker` and `RecoveryManager`**

Implement continuous infinite loop:
`Idea -> Research -> Script -> ScenePlan -> BlenderRender -> Assemble -> QC -> Publish -> Save -> Immediately Repeat`.
Handle restart recovery, rate limit backoff, and daily quota tracking.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_orchestrator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/orchestrator/ backend/tests/test_orchestrator.py
git commit -m "feat(orchestrator): implement continuous autonomous loop and state machine"
```

---

### Task 9: FastAPI Backend Endpoints & Real-Time Event Stream

**Files:**
- Create: `backend/api/routes.py`
- Create: `backend/api/websocket.py`
- Create: `backend/main.py`
- Test: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `AutonomousWorker`, database session, and publishing configs.
- Produces: REST endpoints (`/api/agent/status`, `/api/agent/start`, `/api/agent/pause`, `/api/videos`, `/api/settings`, `/api/channels`) and WebSocket stream at `/ws/events`.

- [ ] **Step 1: Write the failing test for FastAPI Endpoints**

```python
# backend/tests/test_api.py
from fastapi.testclient import TestClient
from backend.main import app

def test_api_status_and_controls():
    client = TestClient(app)
    response = client.get("/api/agent/status")
    assert response.status_code == 200
    data = response.json()
    assert "state" in data
    assert "current_job" in data
    assert "stats" in data
    
    # Test setting update
    update_res = client.post("/api/settings", json={"running_mode": "continuous", "publish_destination": "local"})
    assert update_res.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_api.py -v`
Expected: FAIL with "No module named backend.main"

- [ ] **Step 3: Implement FastAPI application, routes, and WebSocket notifier**

Wire all agent controls, settings mutations, video library listing, OAuth redirect callbacks, and real-time step progress streaming into `backend/main.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/ backend/main.py backend/tests/test_api.py
git commit -m "feat(api): implement FastAPI server, REST routes, and real-time event streaming"
```

---

### Task 10: Modern Autonomous Video Production Dashboard Frontend

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/components/AgentStatusCard.tsx`
- Create: `frontend/src/components/ProductionPipelineVisualizer.tsx`
- Create: `frontend/src/components/CurrentProductionView.tsx`
- Create: `frontend/src/components/VideoLibrary.tsx`
- Create: `frontend/src/components/PlatformAccounts.tsx`
- Create: `frontend/src/components/SettingsModal.tsx`
- Test: `frontend/src/App.test.tsx`

**Interfaces:**
- Consumes: Backend REST API and `/ws/events` WebSocket.
- Produces: Responsive modern glassmorphic dashboard showcasing live continuous operations.

- [ ] **Step 1: Write the frontend component tests**

Create component test in `frontend/src/App.test.tsx` verifying render of Agent status badge, Start/Pause/Stop action buttons, and Pipeline visualizer.

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test` inside `frontend`
Expected: FAIL (files not yet created)

- [ ] **Step 3: Implement React + TypeScript + Tailwind CSS Frontend**

Build components:
1. `AgentStatusCard`: Live status badge (RUNNING, PAUSED, STOPPED), production counters, Start/Pause/Resume/Stop controls.
2. `ProductionPipelineVisualizer`: Visual stepper showing current stage (Discovering -> Researching -> Scripting -> 3D Generating -> Rendering -> QC -> Publishing).
3. `CurrentProductionView`: Real-time active video card showing concept, script, render progress, and preview.
4. `VideoLibrary`: Grid of generated videos with player, platform links, and metadata viewer.
5. `PlatformAccounts`: Connection cards for TikTok and YouTube with OAuth triggers.
6. `SettingsModal`: Customization of destinations, duration, voice, daily limits.

- [ ] **Step 4: Build and test frontend**

Run: `npm run build` in `frontend`
Expected: Successful build with zero errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "feat(ui): implement modern reactive dashboard for continuous video studio"
```

---

### Task 11: End-to-End Autonomous Studio Integration Verification

**Files:**
- Create: `backend/tests/test_e2e_autonomous_loop.py`
- Create: `run_viddy.py`

**Interfaces:**
- Consumes: All backend subsystems, Blender engine, audio engine, compositor, and frontend static bundle.
- Produces: Complete autonomous production execution verifying multiple continuous cycles without manual intervention.

- [ ] **Step 1: Write E2E integration test for autonomous cycle continuation**

```python
# backend/tests/test_e2e_autonomous_loop.py
import pytest
import asyncio
from backend.orchestrator.worker import AutonomousWorker
from backend.database.session import init_db, get_db
from backend.database import crud

@pytest.mark.asyncio
async def test_autonomous_consecutive_productions(tmp_path):
    db_file = tmp_path / "test_e2e.db"
    init_db(str(db_file))
    
    # Configure worker for 2 automated cycles in fast test mode
    worker = AutonomousWorker(
        db_path=str(db_file),
        storage_dir=str(tmp_path / "media"),
        simulated_media=True,
        cycle_delay_seconds=0.1
    )
    
    # Start autonomous worker
    await worker.start()
    
    # Wait for worker to produce at least 2 videos autonomously
    for _ in range(50):
        await asyncio.sleep(0.2)
        with get_db(str(db_file)) as session:
            completed_videos = crud.get_all_videos(session)
            if len(completed_videos) >= 2:
                break
                
    await worker.stop()
    
    with get_db(str(db_file)) as session:
        videos = crud.get_all_videos(session)
        assert len(videos) >= 2
        # Verify titles are distinct (continuous discovery)
        assert videos[0].title != videos[1].title
        # Verify both passed QC and were recorded
        assert all(v.status == "completed" for v in videos[:2])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_e2e_autonomous_loop.py -v`
Expected: FAIL until end-to-end integration is verified.

- [ ] **Step 3: Implement `run_viddy.py` entrypoint and finalize full pipeline wiring**

Ensure graceful startup, automatic Blender & FFmpeg detection and configuration, database auto-migration, and static frontend hosting.

- [ ] **Step 4: Run E2E test to verify it passes**

Run: `python -m pytest backend/tests/test_e2e_autonomous_loop.py -v`
Expected: PASS with 2 consecutive autonomous video productions recorded.

- [ ] **Step 5: Final commit**

```bash
git add .
git commit -m "feat(core): complete fully autonomous AI video production & publishing agent"
```
