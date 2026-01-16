import requests
import os
from pathlib import Path
from config import settings
from typing import Optional
import hashlib


class MusicGenerator:
    """
    Автоматическая генерация/получение музыки
    """
    
    # Бесплатные источники фоновой музыки (royalty-free)
    FREE_MUSIC_LIBRARY = {
        "dramatic": [
            "https://cdn.pixabay.com/download/audio/2022/03/10/audio_2d8e51d58e.mp3?filename=epic-cinematic-trailer-115776.mp3",
            "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=dramatic-cinematic-trailer-121456.mp3",
        ],
        "calm": [
            "https://cdn.pixabay.com/download/audio/2022/08/02/audio_0ab5ab2c5c.mp3?filename=meditation-relaxing-background-music-124758.mp3",
            "https://cdn.pixabay.com/download/audio/2021/08/04/audio_12b0c7443c.mp3?filename=calm-peaceful-ambient-background-music-11221.mp3",
        ],
        "motivational": [
            "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c2f0e5d5a3.mp3?filename=inspiring-cinematic-ambient-116199.mp3",
            "https://cdn.pixabay.com/download/audio/2022/10/18/audio_9b0edfa3e2.mp3?filename=uplifting-motivational-corporate-127852.mp3",
        ],
        "mystical": [
            "https://cdn.pixabay.com/download/audio/2022/05/13/audio_c8c0e0c7e0.mp3?filename=mysterious-ambient-background-120561.mp3",
            "https://cdn.pixabay.com/download/audio/2021/11/26/audio_d1718ab41b.mp3?filename=mystical-ambient-meditation-15045.mp3",
        ],
        "inspiring": [
            "https://cdn.pixabay.com/download/audio/2022/03/24/audio_d1718ab41b.mp3?filename=inspiring-emotional-piano-116199.mp3",
            "https://cdn.pixabay.com/download/audio/2022/08/23/audio_c8c0e0c7e0.mp3?filename=hopeful-inspiring-cinematic-125634.mp3",
        ],
        "sad": [
            "https://cdn.pixabay.com/download/audio/2022/03/10/audio_2d8e51d58e.mp3?filename=sad-emotional-piano-115776.mp3",
            "https://cdn.pixabay.com/download/audio/2021/08/04/audio_12b0c7443c.mp3?filename=melancholic-piano-11221.mp3",
        ],
        "joyful": [
            "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=happy-upbeat-background-121456.mp3",
            "https://cdn.pixabay.com/download/audio/2022/10/18/audio_9b0edfa3e2.mp3?filename=joyful-positive-uplifting-127852.mp3",
        ],
    }
    
    def __init__(self):
        self.music_dir = Path(settings.static_dir) / "music"
        self.music_dir.mkdir(parents=True, exist_ok=True)
    
    async def get_or_download_music(self, mood: str, parable_id: int) -> Optional[str]:
        """
        Получает или скачивает музыку для заданного настроения
        
        Args:
            mood: Настроение (dramatic, calm, etc.)
            parable_id: ID притчи (для уникального имени файла)
        
        Returns:
            Путь к файлу музыки или None
        """
        if mood not in self.FREE_MUSIC_LIBRARY:
            print(f"[Music Generator] Unknown mood: {mood}, using 'dramatic'")
            mood = "dramatic"
        
        # Выбираем первый трек из списка для данного настроения
        music_urls = self.FREE_MUSIC_LIBRARY[mood]
        music_url = music_urls[0]  # Берём первый вариант
        
        # Создаём уникальное имя файла на основе URL и настроения
        url_hash = hashlib.md5(music_url.encode()).hexdigest()[:8]
        filename = f"{mood}_{url_hash}.mp3"
        file_path = self.music_dir / filename
        
        # Если файл уже скачан, возвращаем путь
        if file_path.exists():
            print(f"[Music Generator] Music already exists: {file_path}")
            return str(file_path)
        
        # Скачиваем музыку
        try:
            print(f"[Music Generator] Downloading music for mood '{mood}'...")
            print(f"[Music Generator] URL: {music_url}")
            
            response = requests.get(music_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Сохраняем файл
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"[Music Generator] Music downloaded: {file_path}")
            return str(file_path)
            
        except Exception as e:
            print(f"[Music Generator] Error downloading music: {e}")
            return None
    
    async def generate_music_with_ai(self, mood: str, description: str) -> Optional[str]:
        """
        Генерация музыки через AI (например, Suno AI)
        Пока не реализовано - требует API ключ
        """
        # TODO: Интеграция с Suno AI или другим генератором музыки
        print(f"[Music Generator] AI music generation not implemented yet")
        return None

