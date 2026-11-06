import os
import shutil
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

def find_binary(binary_name: str) -> str:
    """Finds binary in PATH or common Windows installation directories."""
    # 1. In PATH
    found = shutil.which(binary_name)
    if found:
        return found
        
    # 2. Check WinGet packages & LocalAppData
    local_app_data = os.getenv("LOCALAPPDATA", "")
    program_files = os.getenv("ProgramFiles", "")
    
    search_dirs = [
        Path(local_app_data) / "Microsoft" / "WinGet" / "Packages",
        Path(local_app_data) / "Programs",
        Path(program_files),
        Path("C:/ffmpeg")
    ]
    
    for base in search_dirs:
        if base.exists():
            for exe in base.glob(f"**/{binary_name}.exe"):
                if exe.is_file():
                    return str(exe.resolve())
                    
    return binary_name

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")
    
    app_name: str = "Viddy Autonomous AI Video Studio"
    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = base_dir / "data"
    output_dir: Path = base_dir / "output"
    database_url: str = f"sqlite:///{base_dir}/data/viddy.db"
    
    # Defaults
    default_running_mode: str = "continuous" # continuous, limited, paused
    default_destination: str = "local" # local, youtube, tiktok, both
    max_daily_videos: int = 24
    min_cycle_delay_seconds: int = 10
    
    # Media paths
    blender_path: str = os.getenv("BLENDER_PATH", "blender")
    ffmpeg_path: str = os.getenv("FFMPEG_PATH", find_binary("ffmpeg"))
    ffprobe_path: str = os.getenv("FFPROBE_PATH", find_binary("ffprobe"))
    
    # AI API keys
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")

settings = Settings()

# Ensure directories exist
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.output_dir.mkdir(parents=True, exist_ok=True)
