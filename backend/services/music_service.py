from sqlalchemy.orm import Session
from models import MusicTrack, ParableMusic, EnglishParableMusic, Parable, EnglishParable
from typing import Optional
import random
from .music_generator import MusicGenerator


class MusicService:
    
    def __init__(self):
        self.music_generator = MusicGenerator()
    
    def get_music_by_mood(self, mood: str, db: Session) -> Optional[MusicTrack]:
        """
        Получает музыкальный трек по настроению
        """
        tracks = db.query(MusicTrack).filter(
            MusicTrack.mood == mood,
            MusicTrack.is_active == True,
            MusicTrack.file_path.isnot(None)  # Только треки с файлами
        ).all()
        
        if not tracks:
            # Если нет треков с таким настроением, берём любой доступный
            tracks = db.query(MusicTrack).filter(
                MusicTrack.is_active == True,
                MusicTrack.file_path.isnot(None)
            ).all()
        
        return random.choice(tracks) if tracks else None
    
    def detect_mood_from_text(self, text: str, gemini_service) -> str:
        """
        Определяет настроение текста через LLM
        """
        prompt = f"""
Analyze the mood/emotion of this parable text and return ONLY ONE word from this list:
- dramatic (драматичный, напряжённый, эпичный)
- calm (спокойный, умиротворённый, медитативный)
- motivational (мотивационный, вдохновляющий, энергичный)
- mystical (мистический, загадочный, таинственный)
- inspiring (вдохновляющий, поднимающий настроение)
- sad (грустный, печальный, меланхоличный)
- joyful (радостный, весёлый, позитивный)

TEXT:
{text[:500]}

Return ONLY the mood word, nothing else.
"""
        
        from google.genai import types
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            ),
        ]
        
        response = gemini_service.client.models.generate_content(
            model=gemini_service.text_model_name,
            contents=contents,
        )
        
        mood = response.text.strip().lower()
        
        # Валидация - если LLM вернул что-то странное, используем dramatic по умолчанию
        valid_moods = ['dramatic', 'calm', 'motivational', 'mystical', 'inspiring', 'sad', 'joyful']
        if mood not in valid_moods:
            mood = 'dramatic'
        
        return mood
    
    async def assign_music_to_parable(self, parable_id: int, gemini_service, db: Session) -> Optional[MusicTrack]:
        """
        Автоматически подбирает и назначает музыку для притчи
        """
        parable = db.query(Parable).filter(Parable.id == parable_id).first()
        if not parable:
            return None
        
        # Определяем настроение текста
        text = parable.text_for_tts if parable.text_for_tts else parable.text_original
        mood = self.detect_mood_from_text(text, gemini_service)
        
        print(f"[Music Service] Detected mood for parable {parable_id}: {mood}")
        
        # Скачиваем/получаем музыку автоматически
        music_path = await self.music_generator.get_or_download_music(mood, parable_id)
        
        if not music_path:
            print(f"[Music Service] Failed to get music for mood: {mood}")
            return None
        
        # Проверяем есть ли уже трек с таким путём
        music_track = db.query(MusicTrack).filter(MusicTrack.file_path == music_path).first()
        
        if not music_track:
            # Создаём новый трек в БД
            music_track = MusicTrack(
                name=f"Auto-generated {mood.capitalize()} Music",
                file_path=music_path,
                mood=mood,
                is_active=True
            )
            db.add(music_track)
            db.commit()
            db.refresh(music_track)
            print(f"[Music Service] Created new music track: {music_track.name}")
        
        # Проверяем существует ли уже связь
        existing = db.query(ParableMusic).filter(ParableMusic.parable_id == parable_id).first()
        
        if existing:
            # Обновляем существующую связь
            existing.music_track_id = music_track.id
            db.commit()
        else:
            # Создаём новую связь
            parable_music = ParableMusic(
                parable_id=parable_id,
                music_track_id=music_track.id,
                volume_level=-18.0  # Музыка тише голоса на 18dB
            )
            db.add(parable_music)
            db.commit()
        
        print(f"[Music Service] Assigned track '{music_track.name}' to parable {parable_id}")
        
        return music_track
    
    async def assign_music_to_english_parable(self, english_parable_id: int, gemini_service, db: Session) -> Optional[MusicTrack]:
        """
        Автоматически подбирает и назначает музыку для английской версии
        """
        english_parable = db.query(EnglishParable).filter(EnglishParable.id == english_parable_id).first()
        if not english_parable:
            return None
        
        # Определяем настроение текста
        text = english_parable.text_for_tts if english_parable.text_for_tts else english_parable.text_translated
        if not text:
            return None
        
        mood = self.detect_mood_from_text(text, gemini_service)
        
        print(f"[Music Service] Detected mood for English parable {english_parable_id}: {mood}")
        
        # Скачиваем/получаем музыку автоматически
        music_path = await self.music_generator.get_or_download_music(mood, english_parable_id)
        
        if not music_path:
            print(f"[Music Service] Failed to get music for mood: {mood}")
            return None
        
        # Проверяем есть ли уже трек с таким путём
        music_track = db.query(MusicTrack).filter(MusicTrack.file_path == music_path).first()
        
        if not music_track:
            # Создаём новый трек в БД
            music_track = MusicTrack(
                name=f"Auto-generated {mood.capitalize()} Music",
                file_path=music_path,
                mood=mood,
                is_active=True
            )
            db.add(music_track)
            db.commit()
            db.refresh(music_track)
            print(f"[Music Service] Created new music track: {music_track.name}")
        
        # Проверяем существует ли уже связь
        existing = db.query(EnglishParableMusic).filter(
            EnglishParableMusic.english_parable_id == english_parable_id
        ).first()
        
        if existing:
            # Обновляем существующую связь
            existing.music_track_id = music_track.id
            db.commit()
        else:
            # Создаём новую связь
            english_parable_music = EnglishParableMusic(
                english_parable_id=english_parable_id,
                music_track_id=music_track.id,
                volume_level=-18.0
            )
            db.add(english_parable_music)
            db.commit()
        
        print(f"[Music Service] Assigned track '{music_track.name}' to English parable {english_parable_id}")
        
        return music_track

