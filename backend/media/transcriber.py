import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from backend.config import settings

def extract_audio_wav(video_path: str, output_wav_path: str) -> bool:
    """Extracts 16kHz mono WAV audio from a video using FFmpeg."""
    if not os.path.exists(video_path):
        return False

    ffmpeg_bin = settings.ffmpeg_path or shutil.which("ffmpeg")
    if not ffmpeg_bin:
        return False

    Path(output_wav_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(ffmpeg_bin),
        "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(output_wav_path)
    ]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=25)
        return proc.returncode == 0 and os.path.exists(output_wav_path)
    except Exception:
        return False

def transcribe_video_audio(video_path: str) -> str:
    """
    Extracts audio from video and transcribes spoken speech into script text.
    Falls back gracefully if no audio, speech recognition fails, or file is silent.
    """
    if not os.path.exists(video_path):
        return ""

    tmp_wav = Path(video_path).parent / f"{Path(video_path).stem}_audio.wav"
    try:
        ok = extract_audio_wav(video_path, str(tmp_wav))
        if not ok or not tmp_wav.exists() or tmp_wav.stat().st_size < 1000:
            return ""

        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.AudioFile(str(tmp_wav)) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data)
            return text.strip() if text else ""
    except Exception:
        return ""
    finally:
        # Clean up temporary WAV
        try:
            if tmp_wav.exists():
                tmp_wav.unlink(missing_ok=True)
        except Exception:
            pass
