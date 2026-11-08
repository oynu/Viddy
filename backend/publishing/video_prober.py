import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any

from backend.config import settings

def probe_video_metadata(video_path: str) -> Dict[str, Any]:
    """
    Extracts metadata from a video file using ffprobe.
    Returns duration in seconds, width, height, and fps.
    """
    res = {
        "duration": 0.0,
        "width": 0,
        "height": 0,
        "fps": 30.0,
        "has_audio": False,
        "codec": "unknown"
    }

    if not os.path.exists(video_path):
        return res

    ffprobe_bin = settings.ffprobe_path or shutil.which("ffprobe")
    if not ffprobe_bin or not os.path.exists(ffprobe_bin):
        # Fallback if ffprobe binary is not directly available
        return res

    cmd = [
        str(ffprobe_bin),
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(video_path)
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if proc.returncode == 0:
            data = json.loads(proc.stdout)
            format_info = data.get("format", {})
            res["duration"] = float(format_info.get("duration", 0.0))

            for stream in data.get("streams", []):
                codec_type = stream.get("codec_type")
                if codec_type == "video" and res["width"] == 0:
                    res["width"] = int(stream.get("width", 0))
                    res["height"] = int(stream.get("height", 0))
                    res["codec"] = stream.get("codec_name", "unknown")
                    # Calculate FPS
                    r_frame_rate = stream.get("r_frame_rate", "30/1")
                    if "/" in r_frame_rate:
                        num, den = r_frame_rate.split("/")
                        if float(den) > 0:
                            res["fps"] = round(float(num) / float(den), 2)
                elif codec_type == "audio":
                    res["has_audio"] = True
    except Exception:
        pass

    return res

def generate_video_thumbnail(video_path: str, output_thumb_path: str, timestamp_sec: float = 0.5) -> bool:
    """
    Extracts a frame from the video as a JPEG thumbnail using ffmpeg.
    """
    if not os.path.exists(video_path):
        return False

    ffmpeg_bin = settings.ffmpeg_path or shutil.which("ffmpeg")
    if not ffmpeg_bin or not os.path.exists(ffmpeg_bin):
        return False

    out_p = Path(output_thumb_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(ffmpeg_bin),
        "-y",
        "-ss", str(timestamp_sec),
        "-i", str(video_path),
        "-vframes", "1",
        "-q:v", "2",
        str(output_thumb_path)
    ]

    try:
        proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        return proc.returncode == 0 and os.path.exists(output_thumb_path)
    except Exception:
        return False
