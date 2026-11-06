#!/usr/bin/env python3
"""
Viddy — Autonomous AI Video Production & Publishing Studio
Continuous 24/7 autonomous short-form educational video generator.
"""
import os
import sys
import shutil
import uvicorn
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

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
    ffmpeg_cmd = shutil.which("ffmpeg")
    if ffmpeg_cmd:
        print(f"  ✓ FFmpeg detected: {ffmpeg_cmd}")
    else:
        print("  ! FFmpeg not in PATH. Ensure FFmpeg is configured in settings.")

    # Check Blender
    from backend.blender.runner import BlenderRunner
    runner = BlenderRunner()
    if runner.is_blender_available():
        print(f"  ✓ Blender 3D Engine detected: {runner.blender_path}")
    else:
        print("  ! Blender binary not detected on PATH. High-fidelity procedural 3D synthesis fallback will be active.")
        
    print("[2/3] Initializing persistent database...")
    from backend.database.session import init_db
    init_db()
    print("  ✓ Database initialized at data/viddy.db")

def main():
    print_banner()
    check_environment()
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"[3/3] Starting Viddy Autonomous Studio at: http://localhost:{port}")
    print("Press Ctrl+C to terminate studio.")
    
    uvicorn.run("backend.main:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    main()
