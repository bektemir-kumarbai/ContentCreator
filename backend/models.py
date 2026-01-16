from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, func
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
    text_for_tts = Column(Text)
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
    uploaded_at = Column(DateTime, server_default=func.now())
    
    english_parable = relationship("EnglishParable", back_populates="video_fragments")
    image = relationship("EnglishGeneratedImage", back_populates="video_fragments")

