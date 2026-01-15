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
    
    # Финальное видео
    final_video_path = Column(Text)
    final_video_duration = Column(Float)
    completed_at = Column(DateTime)
    
    # Relationships
    image_prompts = relationship("ImagePrompt", back_populates="parable", cascade="all, delete-orphan")
    generated_images = relationship("GeneratedImage", back_populates="parable", cascade="all, delete-orphan")
    audio_files = relationship("AudioFile", back_populates="parable", cascade="all, delete-orphan")
    video_fragments = relationship("VideoFragment", back_populates="parable", cascade="all, delete-orphan")


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

