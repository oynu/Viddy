# Bulk Video Auto-Publisher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform Viddy into a bulk video auto-uploader and multi-platform publisher where users drop their own pre-made videos, configure or auto-generate metadata, and have Viddy autonomously upload and publish the entire batch to TikTok (via Brave), YouTube Shorts (via Google API), or both.

**Architecture:** 
- A FastAPI multipart upload endpoint stores video files in `output/uploads/`, auto-extracts video duration and thumbnail via FFmpeg/FFprobe, and saves video records in the database.
- A sequential background Publish Queue Worker picks up queued videos, loads platform credentials (Brave persistent profile for TikTok, OAuth for YouTube Shorts), sweeps traps, uploads the file, injects captions/hashtags/comments, and posts automatically.
- A smart metadata auto-generator generates viral hooks, TikTok captions, algorithm reach hashtags, and pinned discussion prompts from filenames or quick user prompts.
- A sleek, monochrome, minimalist React dashboard with a drag-and-drop dropzone, batch action buttons ("Auto-Publish All", "Auto-Generate All Metadata"), per-video status tracking, destination switcher (TikTok, YouTube Shorts, Both), and direct links to published posts.

**Tech Stack:**
- Python 3.14, FastAPI, SQLAlchemy (SQLite)
- Playwright (running real Brave Browser) for TikTok Studio automated uploads
- Google API Client (`google-api-python-client`) for YouTube Shorts API
- FFmpeg & FFprobe for metadata extraction & thumbnail generation
- React 18, Vite, TypeScript, Tailwind CSS, Lucide Icons

**Spec:** User mandate: *"upload the files to viddy and it autouploads all of them to tiktok or youtoube or tiktok + yt. But i will make the vids and then have viddy upload them for me. Must work on brave or if its impossible in a place where i dont have to install anythingh¡."*

## Global Constraints
- **Brave Native**: All browser automation must use the user's detected Brave installation (`C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe`).
- **No Manual Installs**: Zero external third-party software installation required by the user. Everything runs using the existing Python virtual environment and local browser.
- **Short-Form Standards**: YouTube Shorts must remain under 60 seconds and include `#Shorts`. TikTok captions must format with hashtags and preserve pinned comments.
- **Resilient Automation**: Purge react-joyride walkthroughs, cookie consent banners, and copyright check traps before every post submission. Clean stale locks before launch.
- **Aesthetic**: Strictly adhere to the minimalist black-and-white monochrome design.

## Review Focus
1. **Multiple video files uploaded simultaneously**: Ensure streaming multipart uploads handle large `.mp4` and `.mov` files without memory exhaustion.
2. **Consecutive TikTok uploads in batch**: Ensure persistent browser context closes cleanly between items, cleans `SingletonLock`, and sweeps Joyride tour overlays so video #2 and beyond publish without freezing.
3. **Missing or custom metadata**: Ensure videos with empty custom captions fall back gracefully to filename-derived titles and standard viral hashtags (`#fyp #foryou #viral`).
4. **Platform-specific failure isolation**: If YouTube Shorts fails (e.g. quota limit), TikTok must still succeed (and vice versa), recording partial success and clear error details without stopping the rest of the batch.
5. **Video preview & direct links**: Ensure uploaded local videos are playable in the UI via the `/media` endpoint and published links navigate directly to TikTok Studio Manage and YouTube Shorts.

---

### Task 1: Multipart File Upload & Video Metadata Probing API

**Files:**
- Create: `backend/publishing/video_prober.py`
- Modify: `backend/api/routes.py`
- Modify: `backend/database/crud.py`
- Test: `backend/tests/test_upload_api.py`

- [ ] **Step 1: Write the failing test for video file probing and upload endpoint**
  Create `backend/tests/test_upload_api.py` testing:
  - Video probing function (`probe_video_file` returning duration, resolution, generating thumbnail).
  - `POST /api/videos/upload` multipart endpoint with mock `.mp4` files.
- [ ] **Step 2: Run test to verify it fails**
  `.\.venv\Scripts\python.exe -m pytest backend/tests/test_upload_api.py -v`
- [ ] **Step 3: Implement `backend/publishing/video_prober.py`**
  - Implement `probe_video_metadata(video_path: str) -> Dict[str, Any]` using FFprobe to get duration, width, height.
  - Implement `generate_video_thumbnail(video_path: str, output_thumb_path: str) -> bool` using FFmpeg.
- [ ] **Step 4: Implement `POST /api/videos/upload` in `backend/api/routes.py`**
  - Accept `files: List[UploadFile]`, destination, optional tags.
  - Save files to `output/uploads/`, probe duration, generate thumbnail.
  - Create `VideoModel` in `data/viddy.db` with status `"ready"`.
- [ ] **Step 5: Run tests and ensure all pass**
  `.\.venv\Scripts\python.exe -m pytest backend/tests/test_upload_api.py -v`
- [ ] **Step 6: Commit Task 1**
  `git add -A; git commit -m "Implement multipart video upload and metadata probing API"`

---

### Task 2: Smart Metadata Auto-Generator Engine

**Files:**
- Create: `backend/publishing/metadata_generator.py`
- Modify: `backend/api/routes.py`
- Test: `backend/tests/test_metadata_generator.py`

- [ ] **Step 1: Write the failing test for metadata generator**
  Create `backend/tests/test_metadata_generator.py` testing:
  - Generating hook title, viral caption, hashtags, pinned comment, and YouTube tags from a filename (e.g. `black_hole_event_horizon.mp4`).
  - `POST /api/videos/{video_id}/auto-metadata` route.
- [ ] **Step 2: Run test to verify it fails**
  `.\.venv\Scripts\python.exe -m pytest backend/tests/test_metadata_generator.py -v`
- [ ] **Step 3: Implement `backend/publishing/metadata_generator.py`**
  - Parse clean topic title from raw filenames.
  - Generate viral opening hook, retention caption, category-targeted hashtags (`#fyp #viral #learnontiktok ...`), pinned engagement comment (e.g., question to boost comment count), and YouTube description + `#Shorts` tags.
- [ ] **Step 4: Add `/api/videos/{video_id}/auto-metadata` and `/api/videos/auto-metadata-all` endpoints**
  - Allow user to auto-generate or regenerate metadata with 1 click.
- [ ] **Step 5: Run tests and ensure all pass**
  `.\.venv\Scripts\python.exe -m pytest backend/tests/test_metadata_generator.py -v`
- [ ] **Step 6: Commit Task 2**
  `git add -A; git commit -m "Implement smart metadata auto-generation engine"`

---

### Task 3: Batch Publishing Queue Engine & Worker

**Files:**
- Create: `backend/publishing/publish_queue.py`
- Modify: `backend/api/routes.py`
- Modify: `backend/orchestrator/worker.py`
- Test: `backend/tests/test_publish_queue.py`

- [ ] **Step 1: Write the failing test for batch queue processor**
  Create `backend/tests/test_publish_queue.py` testing:
  - Enqueuing multiple videos.
  - Sequential processing of queue items calling `PublishingManager`.
  - Updating status to `publishing` -> `completed` / `failed`.
  - Endpoint `POST /api/queue/publish-all` and `POST /api/queue/cancel`.
- [ ] **Step 2: Run test to verify it fails**
  `.\.venv\Scripts\python.exe -m pytest backend/tests/test_publish_queue.py -v`
- [ ] **Step 3: Implement `backend/publishing/publish_queue.py`**
  - Implement `PublishQueue`: an asynchronous, sequential queue processor.
  - Processes one video at a time: checks file exists, checks destination (`tiktok`, `youtube`, `both`), invokes `PublishingManager.publish()`.
  - Cleans profile locks between runs to ensure consecutive Brave uploads succeed without crashing.
  - Updates progress, emits status callbacks, updates DB status and URLs.
- [ ] **Step 4: Integrate queue runner into `backend/api/routes.py`**
  - Wire `/api/queue/status`, `/api/queue/publish-all`, `/api/videos/{video_id}/publish`.
- [ ] **Step 5: Run tests and ensure all pass**
  `.\.venv\Scripts\python.exe -m pytest backend/tests/test_publish_queue.py -v`
- [ ] **Step 6: Commit Task 3**
  `git add -A; git commit -m "Implement batch publishing queue engine"`

---

### Task 4: Bulk Upload & Publishing Studio Frontend

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/index.css` (if needed)
- Test/Build: `npm run build`
- Test: Verify production bundle loads properly.

- [ ] **Step 1: Create drag-and-drop multi-file upload zone**
  - Support multiple file selection (`.mp4`, `.mov`, `.webm`).
  - Visual drag-over feedback, file size, duration indicators.
- [ ] **Step 2: Build Queue Action Controls**
  - Target destination buttons: **TikTok**, **YouTube Shorts**, **Both (TikTok + YouTube)**.
  - Primary button: **"Publish All (N Videos)"** with badge counter.
  - Secondary button: **"Auto-Fill All Metadata"** (generates viral titles/tags for all queued videos).
- [ ] **Step 3: Build Video Queue Cards with inline editing**
  - Editable Title, TikTok Caption & Hashtags, TikTok Pinned Comment.
  - Action buttons: "Publish Now", "Auto-Generate Metadata", "Delete from Queue".
  - Live upload & publishing progress bar with status ("Queued", "Publishing to TikTok via Brave...", "Published", "Error").
  - Direct links to TikTok Studio and YouTube Shorts upon completion.
- [ ] **Step 4: Preserve Brave Session Setup & Account Status**
  - Keep 1-click Brave login launcher with auto-polling so user can connect or refresh their TikTok session anytime.
- [ ] **Step 5: Compile production frontend assets**
  `cmd.exe /c "cd frontend && npm.cmd run build"`
- [ ] **Step 6: Commit Task 4**
  `git add -A; git commit -m "Implement bulk upload and publishing dashboard in frontend"`

---

### Task 5: End-to-End Integration Verification & Regressions

**Files:**
- Run: Full pytest test suite (`backend/tests/`)
- Run: Full frontend build verification

- [ ] **Step 1: Run complete pytest test suite**
  `.\.venv\Scripts\python.exe -m pytest backend/tests/ -v`
- [ ] **Step 2: Verify end-to-end multi-upload flow with mock file**
- [ ] **Step 3: Commit Task 5**
  `git add -A; git commit -m "Verify complete bulk video auto-uploader pipeline"`
