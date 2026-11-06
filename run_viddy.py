#!/usr/bin/env python3
"""
Viddy — Autonomous AI Video Production & Publishing Studio
Continuous 24/7 autonomous short-form educational video generator.
"""
import os
import sys

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

import time
import threading
import webbrowser
import subprocess
from pathlib import Path

# Auto-bootstrap virtualenv: if running with system Python, transparently delegate to .venv
root_dir = Path(__file__).resolve().parent
venv_python = root_dir / ".venv" / "Scripts" / "python.exe" if os.name == "nt" else root_dir / ".venv" / "bin" / "python"

if venv_python.exists():
    try:
        current_python = Path(sys.executable).resolve()
        target_python = venv_python.resolve()
        if current_python != target_python:
            # Re-execute seamlessly under the isolated virtual environment
            exit_code = subprocess.call([str(target_python), str(__file__)] + sys.argv[1:])
            sys.exit(exit_code)
    except Exception:
        pass

# Add project root to sys.path
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import shutil

def print_banner():
    banner = r"""
  __      ___     _     _       
  \ \    / (_)   | |   | |      
   \ \  / / _  __| | __| |_   _ 
    \ \/ / | |/ _` |/ _` | | | |
     \  /  | | (_| | (_| | |_| |
      \/   |_|\__,_|\__,_|\__, |
                           __/ |
                          |___/ 
   AUTONOMOUS 24/7 AI VIDEO STUDIO
   ---------------------------------
    """
    print(banner)

def check_environment():
    print("[1/3] Checking environment...")
    
    # Check FFmpeg
    from backend.config import settings
    if settings.ffmpeg_path and Path(settings.ffmpeg_path).exists():
        print(f"  [OK] FFmpeg detected: {settings.ffmpeg_path}")
    elif shutil.which("ffmpeg"):
        print(f"  [OK] FFmpeg detected in PATH: {shutil.which('ffmpeg')}")
    else:
        print("  [!] FFmpeg not detected. Please verify installation.")

    # Check Blender
    from backend.blender.runner import BlenderRunner
    runner = BlenderRunner()
    if runner.is_blender_available():
        print(f"  [OK] Blender 3D Engine detected: {runner.blender_path}")
    else:
        print("  [!] Blender binary not detected on PATH. High-fidelity procedural 3D synthesis fallback active.")
        
    print("[2/3] Initializing persistent database...")
    from backend.database.session import init_db, get_db
    from backend.database import crud
    init_db()
    with get_db() as session:
        st = crud.get_settings(session)
        pref_str = st.publish_destination.upper()
        print(f"  [OK] Database initialized at data/viddy.db")
        print(f"  [OK] Configured Publishing Destination: [{pref_str}]")
        print(f"       (You can change destination to YouTube, TikTok, Both or Local in the Studio UI)")

def auto_open_browser(url: str):
    """Waits for uvicorn server to start and opens default browser."""
    time.sleep(1.8)
    try:
        webbrowser.open(url)
    except Exception:
        pass

def main():
    print_banner()
    check_environment()
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    studio_url = f"http://localhost:{port}"
    
    print(f"[3/3] Starting Viddy Autonomous Studio at: {studio_url}")
    print(f"  [OK] Auto-opening Web Studio Dashboard in browser: {studio_url}")
    print("  [OK] Real-time autonomous AI agents streaming live in terminal below:")
    print("----------------------------------------------------------------------")
    
    # Launch browser thread
    threading.Thread(target=auto_open_browser, args=(studio_url,), daemon=True).start()
    
    import uvicorn
    uvicorn.run("backend.main:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    main()
