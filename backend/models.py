from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from database import Base


class Parable(Base):
    __tablename__ = "parables"
    
    id = Column(Integer, primary_key=True, index=True)
    title_original = Column(Text, nullable=False)
    text_original = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Обработанные данные
    text_for_tts = Column(Text)
    hook_text = Column(Text)  # Цепляющее начало для первых 3 секунд
    youtube_title = Column(Text)
    youtube_description = Column(Text)
    youtube_hashtags = Column(Text)
    
    # Метаданные
    processed_at = Column(DateTime)
    status = Column(String(50), default='draft')
    current_step = Column(Integer, default=0)  # Текущий шаг обработки (0-4)
    error_message = Column(Text)  # Сообщение об ошибке
    
    # Финальное видео
    final_video_path = Column(Text)
    final_video_duration = Column(Float)
    completed_at = Column(DateTime)
    
    # Relationships
    image_prompts = relationship("ImagePrompt", back_populates="parable", cascade="all, delete-orphan")
    generated_images = relationship("GeneratedImage", back_populates="parable", cascade="all, delete-orphan")
    audio_files = relationship("AudioFile", back_populates="parable", cascade="all, delete-orphan")
    video_fragments = relationship("VideoFragment", back_populates="parable", cascade="all, delete-orphan")
    english_version = relationship("EnglishParable", back_populates="parable", uselist=False, cascade="all, delete-orphan")


class ImagePrompt(Base):
    __tablename__ = "image_prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    parable_id = Column(Integer, ForeignKey("parables.id"), nullable=False)
    prompt_text = Column(Text, nullable=False)
    video_prompt_text = Column(Text, nullable=False)
    scene_order = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    parable = relationship("Parable", back_populates="image_prompts")
    generated_images = relationship("GeneratedImage", back_populates="prompt", cascade="all, delete-orphan")


class GeneratedImage(Base):
    __tablename__ = "generated_images"
    
    id = Column(Integer, primary_key=True, index=True)
    parable_id = Column(Integer, ForeignKey("parables.id"), nullable=False)
    prompt_id = Column(Integer, ForeignKey("image_prompts.id"), nullable=False)
    image_path = Column(Text, nullable=False)
    scene_order = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    parable = relationship("Parable", back_populates="generated_images")
    prompt = relationship("ImagePrompt", back_populates="generated_images")
    video_fragments = relationship("VideoFragment", back_populates="image")


class AudioFile(Base):
    __tablename__ = "audio_files"
    
    id = Column(Integer, primary_key=True, index=True)
    parable_id = Column(Integer, ForeignKey("parables.id"), nullable=False)
    audio_path = Column(Text, nullable=False)
    duration = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    
    parable = relationship("Parable", back_populates="audio_files")


class VideoFragment(Base):
    __tablename__ = "video_fragments"
    
    id = Column(Integer, primary_key=True, index=True)
    parable_id = Column(Integer, ForeignKey("parables.id"), nullable=False)
    image_id = Column(Integer, ForeignKey("generated_images.id"))
    video_path = Column(Text, nullable=False)
    scene_order = Column(Integer, nullable=False)
    duration = Column(Float)
    target_duration = Column(Float)  # Целевая длительность (для ускорения/замедления)
    uploaded_at = Column(DateTime, server_default=func.now())
    
    parable = relationship("Parable", back_populates="video_fragments")
    image = relationship("GeneratedImage", back_populates="video_fragments")


# ═══════════════════════════════════════════════════════════════
# ENGLISH VERSION MODELS
# ═══════════════════════════════════════════════════════════════

class EnglishParable(Base):
    __tablename__ = "english_parables"
    
    id = Column(Integer, primary_key=True, index=True)
    parable_id = Column(Integer, ForeignKey("parables.id"), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Переведённые данные
    title_translated = Column(Text)  # Переведённый заголовок
    text_translated = Column(Text)   # Переведённый текст
    text_for_tts = Column(Text)
    hook_text = Column(Text)  # Catchy hook for first 3 seconds
    youtube_title = Column(Text)
    youtube_description = Column(Text)
    youtube_hashtags = Column(Text)
    
    # Метаданные
    processed_at = Column(DateTime)
    status = Column(String(50), default='draft')
    current_step = Column(Integer, default=0)
    error_message = Column(Text)
    
    # Финальное видео
    final_video_path = Column(Text)
    final_video_duration = Column(Float)
    completed_at = Column(DateTime)
    
    # Relationships
    parable = relationship("Parable", back_populates="english_version")
    image_prompts = relationship("EnglishImagePrompt", back_populates="english_parable", cascade="all, delete-orphan")
    generated_images = relationship("EnglishGeneratedImage", back_populates="english_parable", cascade="all, delete-orphan")
    audio_files = relationship("EnglishAudioFile", back_populates="english_parable", cascade="all, delete-orphan")
    video_fragments = relationship("EnglishVideoFragment", back_populates="english_parable", cascade="all, delete-orphan")


class EnglishImagePrompt(Base):
    __tablename__ = "english_image_prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    english_parable_id = Column(Integer, ForeignKey("english_parables.id"), nullable=False)
    prompt_text = Column(Text, nullable=False)
    video_prompt_text = Column(Text, nullable=False)
    scene_order = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    english_parable = relationship("EnglishParable", back_populates="image_prompts")
    generated_images = relationship("EnglishGeneratedImage", back_populates="prompt", cascade="all, delete-orphan")


class EnglishGeneratedImage(Base):
    __tablename__ = "english_generated_images"
    
    id = Column(Integer, primary_key=True, index=True)
    english_parable_id = Column(Integer, ForeignKey("english_parables.id"), nullable=False)
    prompt_id = Column(Integer, ForeignKey("english_image_prompts.id"), nullable=False)
    image_path = Column(Text, nullable=False)
    scene_order = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    english_parable = relationship("EnglishParable", back_populates="generated_images")
    prompt = relationship("EnglishImagePrompt", back_populates="generated_images")
    video_fragments = relationship("EnglishVideoFragment", back_populates="image")


class EnglishAudioFile(Base):
    __tablename__ = "english_audio_files"
    
    id = Column(Integer, primary_key=True, index=True)
    english_parable_id = Column(Integer, ForeignKey("english_parables.id"), nullable=False)
    audio_path = Column(Text, nullable=False)
    duration = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    
    english_parable = relationship("EnglishParable", back_populates="audio_files")


class EnglishVideoFragment(Base):
    __tablename__ = "english_video_fragments"
    
    id = Column(Integer, primary_key=True, index=True)
    english_parable_id = Column(Integer, ForeignKey("english_parables.id"), nullable=False)
    image_id = Column(Integer, ForeignKey("english_generated_images.id"))
    video_path = Column(Text, nullable=False)
    scene_order = Column(Integer, nullable=False)
    duration = Column(Float)
    target_duration = Column(Float)  # Целевая длительность (для ускорения/замедления)
    uploaded_at = Column(DateTime, server_default=func.now())
    
    english_parable = relationship("EnglishParable", back_populates="video_fragments")
    image = relationship("EnglishGeneratedImage", back_populates="video_fragments")


# ═══════════════════════════════════════════════════════════════
# MUSIC SYSTEM MODELS
# ═══════════════════════════════════════════════════════════════

class MusicTrack(Base):
    __tablename__ = "music_tracks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    file_path = Column(Text)  # Путь к музыкальному файлу
    mood = Column(String(50), nullable=False)  # dramatic, calm, motivational, etc.
    duration = Column(Float)
    bpm = Column(Integer)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    parable_music = relationship("ParableMusic", back_populates="music_track")
    english_parable_music = relationship("EnglishParableMusic", back_populates="music_track")


class ParableMusic(Base):
    __tablename__ = "parable_music"
    
    id = Column(Integer, primary_key=True, index=True)
    parable_id = Column(Integer, ForeignKey("parables.id"), nullable=False, unique=True)
    music_track_id = Column(Integer, ForeignKey("music_tracks.id"))
    volume_level = Column(Float, default=-18.0)  # dB относительно голоса
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    parable = relationship("Parable")
    music_track = relationship("MusicTrack", back_populates="parable_music")


class EnglishParableMusic(Base):
    __tablename__ = "english_parable_music"
    
    id = Column(Integer, primary_key=True, index=True)
    english_parable_id = Column(Integer, ForeignKey("english_parables.id"), nullable=False, unique=True)
    music_track_id = Column(Integer, ForeignKey("music_tracks.id"))
    volume_level = Column(Float, default=-18.0)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    english_parable = relationship("EnglishParable")
    music_track = relationship("MusicTrack", back_populates="english_parable_music")


# ═══════════════════════════════════════════════════════════════
# A/B TESTING MODELS
# ═══════════════════════════════════════════════════════════════

class TitleVariant(Base):
    __tablename__ = "title_variants"
    
    id = Column(Integer, primary_key=True, index=True)
    parable_id = Column(Integer, ForeignKey("parables.id"), nullable=False)
    variant_text = Column(Text, nullable=False)
    variant_type = Column(String(50), nullable=False)  # question, intrigue, emotion, numbers, provocation
    is_selected = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    parable = relationship("Parable")


class EnglishTitleVariant(Base):
    __tablename__ = "english_title_variants"
    
    id = Column(Integer, primary_key=True, index=True)
    english_parable_id = Column(Integer, ForeignKey("english_parables.id"), nullable=False)
    variant_text = Column(Text, nullable=False)
    variant_type = Column(String(50), nullable=False)
    is_selected = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    english_parable = relationship("EnglishParable")

