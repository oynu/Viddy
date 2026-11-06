import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

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
    ffmpeg_path: str = os.getenv("FFMPEG_PATH", "ffmpeg")
    
    # AI API keys
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")

settings = Settings()

# Ensure directories exist
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.output_dir.mkdir(parents=True, exist_ok=True)
