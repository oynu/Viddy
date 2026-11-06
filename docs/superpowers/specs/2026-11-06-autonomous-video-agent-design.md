# Viddy: Fully Autonomous AI Video Production & Publishing Agent - System Architecture & Design

## 1. Executive Overview

**Viddy** is an autonomous 24/7 AI video studio designed for continuous, hands-off short-form video creation and publishing. Unlike single-shot video generation tools that require manual approval after every phase, Viddy executes an infinite, resilient production loop:
1. Discovering original, engaging educational concepts (physics, astronomy, biology, AI, etc.) with duplicate-avoidance memory.
2. Conducting deep scientific research and verifying facts.
3. Writing viral narrative scripts with hooks, pacing, and synchronized narration.
4. Synthesizing voiceover (via multi-provider audio engine: Edge-TTS / ElevenLabs) and generating word-accurate subtitles.
5. Programmatically generating and rendering cinematic low-poly 3D animations using Blender via Python.
6. Assembling final 9:16 vertical MP4s (1080x1920 @ 30fps) with FFmpeg.
7. Running automated Quality Control (QC) checks on audio/video sync, frame integrity, and duration.
8. Automatically publishing to TikTok, YouTube Shorts, or local storage using official OAuth APIs.
9. Storing results in a persistent SQLite database and video library.
10. Instantly initiating the next production cycle without waiting for user input.

---

## 2. System Architecture

```
+-----------------------------------------------------------------------------------+
|                                 Viddy Frontend UI                                 |
|         (React + Vite + Tailwind CSS + Lucide Icons + Live WebSocket/Polling)      |
+------------------------------------------+----------------------------------------+
                                           | HTTP / REST & WebSockets
+------------------------------------------v----------------------------------------+
|                                FastAPI Backend Engine                             |
|  - REST Endpoints (Agent controls, Queue, Library, Settings, OAuth Connectors)    |
|  - Real-time Event Stream / Status Broadcasting                                   |
|  - Persistent SQLite Database (Jobs, Videos, Ideas, Channels, Settings, Logs)     |
+------------------------------------------+----------------------------------------+
                                           | Orchestration Bus
+------------------------------------------v----------------------------------------+
|                     Continuous Orchestration Engine (Worker Loop)                |
|  State Machine: IDLE -> DISCOVER -> RESEARCH -> SCRIPT -> SCENE_PLAN ->          |
|                 RENDER_3D -> AUDIO_ASSEMBLY -> QC -> PUBLISH -> COMPLETE         |
|  - Survives app restarts, tracks production quotas & daily limits                 |
|  - Error recovery, retry with backoff, anti-stall watchdog                        |
+------------------------------------------+----------------------------------------+
                                           | Dispatches Sub-Agents
     +-------------------+-----------------+------------------+-----------------+
     |                   |                 |                  |                 |
+----v-----+       +-----v----+      +-----v----+       +-----v----+      +-----v----+
|   Idea   |       | Research |      |  Script  |       |  Visual  |      | Quality  |
|Discovery |       |  Agent   |      |  Agent   |       | Director |      | Control  |
+----------+       +----------+      +----------+       +----------+      +----------+
     |                   |                 |                  |                 |
+----v-------------------v-----------------v------------------v-----------------v----+
|                          Core Media Production Pipeline                            |
|  1. Blender 3D Production Engine (Headless Python scripts, low-poly procedural     |
|     geometry, cinematic lighting, material shaders, 9:16 cameras, 30fps render)    |
|  2. Audio Synthesis Engine (Edge-TTS / ElevenLabs, audio normalization, BGM mix)   |
|  3. Subtitle Engine (SRT/ASS generation with word-level highlight animations)     |
|  4. FFmpeg Video Compositor (Color grading, audio-video muxing, H.264 encode)      |
+------------------------------------------+----------------------------------------+
                                           | QC Passed
+------------------------------------------v----------------------------------------+
|                          Autonomous Publishing Engine                             |
|  - YouTube Data API v3 (OAuth2 token refresh, resumable upload, Shorts metadata)  |
|  - TikTok Content Posting API v2 (Creator auth, direct upload, captioning)       |
|  - Local Storage Publisher (Organized archival with full metadata JSON & assets)  |
+-----------------------------------------------------------------------------------+
```

---

## 3. Core Subsystems

### 3.1 Idea Discovery & Creative Director Agent
- Maintains a SQLite memory of all past topics, hooks, and keywords to guarantee zero repetition.
- Generates high-curiosity concepts across 8 key educational domains:
  1. Astrophysics & Space ("What if the Moon disappeared?")
  2. Quantum Mechanics & Physics ("What if gravity doubled?")
  3. Biology & Neuroscience ("How does a synapse fire in milliseconds?")
  4. Chemistry & Materials ("Why doesn't glass freeze into crystals?")
  5. AI & Future Tech ("How does an artificial neural network remember?")
  6. Earth Sciences & Cataclysms ("What happens inside a supervolcano?")
  7. Mathematics & Paradoxes ("The Gabriel's Horn paradox explained")
  8. Everyday Science ("Why does ice float on water?")
- Evaluates candidates using an internal scoring matrix: Curiosity (0-10), Visual Potential (0-10), Scientific Reliability (0-10).

### 3.2 Research & Scriptwriting Agent
- Extracts verified scientific mechanisms, distinguishing proven laws from theoretical models.
- Generates:
  - Viral opening hook (first 3 seconds).
  - High-retention narration script (30-60s duration, ~75-130 words).
  - Scene-by-scene visual instructions with timing cues.
  - Subtitle cues and on-screen emphasis keywords.
  - Citations and platform-tailored tags/descriptions.

### 3.3 Blender Low-Poly 3D Production Engine
- Operates Blender in headless background mode (`blender -b -P script.py`).
- Maintains a modular library of procedural low-poly generator templates:
  - `SpaceGenerator`: Procedural planets, asteroid belts, orbital camera fly-arounds, black hole accretion disks with gravitational lensing distortion, stellar nebulas.
  - `PhysicsGenerator`: Dynamic rigid body physics, collisions, particle streams, fluid-like low-poly simulations, force field gravity wells.
  - `MicroGenerator`: Procedural DNA double helix, glowing neuron synaptic nodes with pulse impulses, cell membranes, viral capsids.
  - `TechGenerator`: Cybernetic circuits, glowing data streams, server matrices, AI core nodes.
  - `AtmosphereGenerator`: Volcanic eruptions, ocean wave low-poly meshes, weather phenomena.
- Camera: Vertical 9:16 framing (1080x1920), 3-point cinematic lighting with soft shadows, rim lighting, ambient occlusion, depth of field, and smooth Bezier camera animations.
- Output: 30 FPS PNG sequence or direct MP4 render.

### 3.4 Audio & Subtitle Engine
- **Voice synthesis**: Free, high-quality Edge-TTS (`en-US-ChristopherNeural`, `en-US-JennyNeural`, etc.) with fallback to ElevenLabs or system TTS.
- **Subtitles**: Auto-generates vertical kinetic subtitles with custom typography, contrasting stroke, and karaoke word highlights burnt in or muxed via FFmpeg.
- **Background Audio**: Procedural ambient synth or royalty-free audio tracks mixed at -18dB under clear voiceover.

### 3.5 Quality Control Agent (Autonomous Gatekeeper)
Automated multi-point inspection before any publishing action:
1. Video existence and file size (> 100 KB).
2. Exact resolution check: 1080 width x 1920 height.
3. Frame count and duration validation (within configured 20-75s target).
4. Audio stream verification: valid AAC/MP3 track present, non-zero audio levels, no clipping.
5. Visual defect check: samples frames to ensure no pitch-black frames, missing render artifacts, or single-color rendering crashes.
6. Repair strategy: If QC fails, analyzes the failure point (e.g., render crash vs audio failure) and re-executes the failed stage with adjusted parameters up to 2 retries before quarantining and advancing to the next topic.

### 3.6 Continuous Autonomous Orchestration Engine
- Persistent state machine running in an independent background worker.
- Persistent SQLite database stores:
  - `videos`: id, title, script, topic, duration, status, paths, published_urls, created_at.
  - `production_jobs`: queue of current and upcoming jobs.
  - `ideas_history`: memory of past topics, hooks, and keywords.
  - `agent_settings`: running_mode (continuous, limited, paused), max_daily_videos, destinations (tiktok, youtube, both, local), api_keys, limits.
  - `platform_credentials`: OAuth tokens, refresh tokens, expiry for YouTube & TikTok.
  - `production_logs`: timestamped live logging stream for dashboard.
- Survives process restarts: when backend boots, it checks for active/interrupted jobs, marks stale jobs for recovery, and immediately resumes continuous operation if state is "RUNNING".

### 3.7 Autonomous Publishing Engine
- **YouTube Shorts API**: YouTube Data API v3 upload endpoint with resumable chunked upload, `#Shorts` category tag, auto-title, description with citations, and privacy setting (public / unlisted / private).
- **TikTok API**: TikTok Content Posting API v2 with Creator OAuth authorization, video direct upload, caption with hashtags.
- **Local Storage Publisher**: Automatically exports videos to `output/videos/{date}_{slug}/` with thumbnail, metadata.json, script.txt, and render logs.

### 3.8 Modern Dashboard Interface
- React + Tailwind CSS + Lucide icons.
- **Agent Status Bar**: Big visual indicator (RUNNING / PAUSED / STOPPED / RECOVERING) with single-click Start, Pause, Resume, Stop controls.
- **Live Activity Pipeline**: Step-by-step illuminated visual stepper (Idea -> Research -> Script -> 3D Scene -> Rendering -> QC -> Publishing).
- **Active Job Monitor**: Live preview of video currently being made, current stage logs, progress percentage.
- **Video Library**: Grid and list views of completed videos with embedded video player, copyable publication URLs, metadata inspector, and download buttons.
- **Platform Connection Hub**: Direct OAuth connection cards for YouTube and TikTok showing status, channel name, token expiration, and reconnect triggers.
- **Settings & Limits**: Frequency controls (videos/day, delay between videos), voice selection, rendering quality, AI API keys.

---

## 4. Technology Stack
- **Backend**: Python 3.11+ / 3.14+, FastAPI, Uvicorn, SQLAlchemy / SQLite, aiosqlite, Pydantic, HTTPX.
- **3D Production**: Blender (Headless CLI + Python `bpy`), FFmpeg.
- **Voice & Audio**: `edge-tts`, `soundfile` / `pydub`.
- **Frontend**: Vite, React 19 / TypeScript, Tailwind CSS, Lucide React.
- **APIs**: Google YouTube Data API v3, TikTok Content Posting API v2, Gemini / OpenAI SDKs.
