from pydantic_settings import BaseSettings
from pathlib import Path
import os


# Определяем базовую директорию проекта
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://admin:admin123@localhost:5111/contentcreator"
    
    # API Keys
    gemini_api_key: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    
    # Directories
    upload_dir: Path = Path("./uploads")
    output_dir: Path = Path("./outputs")
    
    # Gemini models
    gemini_text_model: str = "gemini-3-pro-preview"
    gemini_image_model: str = "gemini-2.5-flash-image"
    
    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = 'utf-8'
        case_sensitive = False
        extra = 'ignore'  # Игнорируем лишние переменные из .env


settings = Settings()

# Создаём директории если их нет
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.output_dir.mkdir(parents=True, exist_ok=True)
(settings.upload_dir / "images").mkdir(exist_ok=True)
(settings.upload_dir / "audio").mkdir(exist_ok=True)
(settings.upload_dir / "videos").mkdir(exist_ok=True)
(settings.output_dir / "final").mkdir(exist_ok=True)

