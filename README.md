# Viddy — Bulk Video Auto-Publisher & Short-Form Studio

**Viddy** is a local, privacy-first studio that automates short-form video publishing to **TikTok** and **YouTube Shorts**. Simply drag and drop your video files: Viddy extracts and transcribes spoken dialogue, crafts high-retention viral hooks, captions, and hashtags, and publishes the batch through your native browser (**Brave, Chrome, Edge, Chromium**) in the background.

Designed with an Apple-inspired **Liquid Glass** monochrome interface.

---

## ⚡ Highlights

- **Multi-Browser Auto-Detection Engine**:
  - Automatically discovers installed Chromium browsers on **Windows, macOS, and Linux**:
    1. **Brave Browser** (recommended for anti-fingerprint shield & ad-blocking)
    2. **Google Chrome**
    3. **Microsoft Edge**
    4. **Chromium**
    5. **Playwright Bundled Engine** (automatic fallback if no desktop browser is detected)
  - Custom browser override supported via `BROWSER_PATH` or `BRAVE_PATH` environment variables.
  - Auto-cleans stale profile locks (`SingletonLock`) to prevent session lockouts and browser crashes.
  - Handles cookie dialogs, Joyride walkthrough overlays, and audio copyright modals autonomously.
- **Bulk Video Import & Instant Drop**:
  - Drag and drop `.mp4`, `.mov`, `.webm`, `.mkv`, `.avi`, or `.m4v` video files in batches.
- **Speech-to-Text Transcription**:
  - Automatically isolates audio tracks and extracts spoken scripts via speech recognition.
- **Viral Metadata Generator**:
  - **Hook Titles**: High-CTR opening headlines tailored to your content.
  - **Retention Captions**: Algorithm-optimized descriptions.
  - **Reach Hashtags**: Broad discovery tags (`#fyp #viral #trending`) blended with niche topic tags.
  - **Pinned Comments**: Thought-provoking discussion prompts to maximize reply velocity.
- **YouTube Shorts Integration**:
  - Automatically routes vertical 9:16 videos under 60 seconds with `#Shorts` tags via the official Google Data API.
- **Apple-Inspired Liquid Glass Interface**:
  - Minimalist black-and-white aesthetic with frosted glass surfaces (`backdrop-blur-2xl`), specular edge highlights, and subtle ambient depth.
- **Privacy-First & Fully Local**:
  - Operates 100% on your machine. No mandatory third-party subscriptions or cloud data leakage.

---

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.10+** (Python 3.12+ recommended)
- **A modern web browser** (Brave, Google Chrome, Microsoft Edge, or Chromium)
- **FFmpeg** in your system PATH:
  ```powershell
  # Windows via WinGet
  winget install Gyan.FFmpeg
  ```

### 2. Installation

Clone this repository and set up your Python environment:

```bash
git clone https://github.com/oynu/Viddy.git
cd Viddy

# Create and activate virtual environment
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Launching Viddy

On Windows, double-click **`run_viddy.bat`** or run:

```bash
python run_viddy.py
```

The studio will start and automatically launch at:
```
http://localhost:8000
```

---

## 🛠️ Usage

1. **Connect TikTok Session**:
   - In the top header, click **Connect TikTok in [Browser]**.
   - Your detected browser opens to TikTok Studio. Log in once to save your session cookies locally in `data/`.
   - All subsequent uploads run autonomously in the background.

2. **Select Upload Target**:
   - Choose **TikTok**, **YouTube Shorts**, or **Both**.

3. **Drop Videos**:
   - Drag and drop your video files into the liquid glass drop zone.
   - If **⚡ Auto-post immediately upon drop** is checked, Viddy transcribes the speech, generates viral metadata, and queues publishing automatically.
   - You can also manually adjust generated captions, tags, and pinned comments before clicking **Upload & Post All**.

---

## 🔒 Privacy & Security

- **Strict File Upload Validation**: Whitelist enforcement (`.mp4`, `.mov`, `.webm`, `.mkv`, `.avi`, `.m4v`), regex stem sanitization, and path traversal guards.
- **Shielded Credentials**: Cookies, OAuth tokens, and session caches are stored exclusively on your local machine and strictly git-ignored.
- **Zero Telemetry**: No user analytics, tracker pings, or external data sharing.

---

## 👥 Contributors

- **[@oynu](https://github.com/oynu)** — Creator & Project Lead
- **[Antigravity](https://github.com/google-deepmind)** (Google DeepMind) — Core Architecture, Multi-Browser Engine & Security Hardening

---

## 📄 License

MIT License. Free for personal and commercial content automation.
