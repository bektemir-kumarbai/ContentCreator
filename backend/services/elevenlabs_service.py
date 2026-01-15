from elevenlabs import generate, save, Voice, VoiceSettings
from config import settings
from pathlib import Path
from pydub import AudioSegment


class ElevenLabsService:
    def __init__(self):
        self.api_key = settings.elevenlabs_api_key
        self.voice_id = settings.elevenlabs_voice_id
    
    async def generate_audio(self, text: str, parable_id: int) -> tuple[str, float]:
        """
        Генерирует аудио из текста с эмоциональными тегами
        Возвращает путь к файлу и длительность в секундах
        """
        audio_dir = settings.upload_dir / "audio" / str(parable_id)
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        audio_path = audio_dir / "narration.mp3"
        
        # Генерируем аудио через ElevenLabs
        audio = generate(
            text=text,
            voice=Voice(
                voice_id=self.voice_id,
                settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.5,
                    use_speaker_boost=True
                )
            ),
            model="eleven_multilingual_v2",
            api_key=self.api_key
        )
        
        # Сохраняем аудио
        save(audio, str(audio_path))
        
        # Получаем длительность
        audio_segment = AudioSegment.from_mp3(str(audio_path))
        duration = len(audio_segment) / 1000.0  # в секундах
        
        return str(audio_path), duration

