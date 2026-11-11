# Viddy — Bulk Video Auto-Publisher & Short-Form Studio

**Viddy** is a local, privacy-first studio that automates short-form video publishing to **TikTok** and **YouTube Shorts**. Simply drag and drop your video files: Viddy automatically transcribes the audio, crafts high-retention viral captions and hashtags, and publishes the batch through your native **Brave Browser** in the background.

---

## ⚡ Highlights

- **Bulk Video Import**: Drag and drop as many `.mp4`, `.mov`, or `.webm` files as you want at once.
- **Audio Script Transcription**: Automatically extracts audio tracks and transcribes spoken speech into text using speech recognition.
- **Viral Metadata Generator**:
  - **Hook Titles**: Attention-grabbing opening titles.
  - **Retention Captions**: Algorithm-optimized descriptions.
  - **Reach Hashtags**: Broad discovery tags (`#fyp #viral #trending`) + niche topic tags.
  - **Pinned Comments**: Thought-provoking discussion starters to boost engagement and reply count.
- **Brave Browser Automation**:
  - Runs natively through your installed Brave Browser via Playwright.
  - Auto-bypasses cookie banners, Joyride tour overlays, and sound copyright check popups.
  - Keeps your session persistent across consecutive uploads without crashing.
- **YouTube Shorts Integration**: Automatically routes 9:16 videos under 60 seconds with `#Shorts` tags via the official Google Data API.
- **Zero Third-Party Accounts Required**: Operates 100% locally on your machine with free local engines (Edge-TTS, FFmpeg, Brave Browser).
- **Ultra-Minimalist Dashboard**: Clean, responsive black-and-white interface.

---

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.10+** (Python 3.12+ recommended)
- **Brave Browser** installed on your system
- **FFmpeg** in your system PATH (or installed via WinGet: `winget install Gyan.FFmpeg`)

### 2. Installation

Clone this repository and set up a virtual environment:

```bash
git clone https://github.com/your-username/viddy.git
cd viddy

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Launching Viddy

On Windows, simply double-click **`run_viddy.bat`** or run:

```bash
python run_viddy.py
```

The studio will start and automatically open in your default browser at:
```
http://localhost:8000
```

---

## 🛠️ Usage

1. **Connect TikTok Session**:
   - In the header, click **Connect TikTok in Brave**.
   - A Brave window will open to TikTok Studio. Log in once to save your session locally.
   - Subsequent uploads run autonomously in the background.

2. **Select Upload Target**:
   - Choose **TikTok (via Brave)**, **YouTube Shorts**, or **Both**.

3. **Drop Videos**:
   - Drag and drop your `.mp4` or `.mov` files into the drop box.
   - If **⚡ Auto-post immediately upon drop** is checked, Viddy automatically analyzes the script, crafts captions and hashtags, and begins publishing immediately.
   - Otherwise, review and edit captions in the dashboard, then click **Upload & Post All**.

---

## 🔒 Privacy & Security

- **Local Storage Only**: All video files, session tokens, and database entries are stored locally in `data/` and `output/`.
- **Git Shielded**: All credentials, session caches, and generated media are strictly git-ignored and never committed or transmitted to any external server.

---

## 📄 License

MIT License. Free for personal and commercial content automation.
