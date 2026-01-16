from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ParableCreate(BaseModel):
    title_original: str
    text_original: str


class ParableResponse(BaseModel):
    id: int
    title_original: str
    text_original: str
    created_at: datetime
    text_for_tts: Optional[str] = None
    youtube_title: Optional[str] = None
    youtube_description: Optional[str] = None
    youtube_hashtags: Optional[str] = None
    status: str
    current_step: Optional[int] = 0
    error_message: Optional[str] = None
    final_video_path: Optional[str] = None
    final_video_duration: Optional[float] = None
    
    class Config:
        from_attributes = True


class ImagePromptResponse(BaseModel):
    id: int
    parable_id: int
    prompt_text: str
    scene_order: int
    
    class Config:
        from_attributes = True


class GeneratedImageResponse(BaseModel):
    id: int
    parable_id: int
    prompt_id: int
    image_path: str
    scene_order: int
    
    class Config:
        from_attributes = True


class AudioFileResponse(BaseModel):
    id: int
    parable_id: int
    audio_path: str
    duration: Optional[float] = None
    
    class Config:
        from_attributes = True


class VideoFragmentResponse(BaseModel):
    id: int
    parable_id: int
    image_id: Optional[int] = None
    video_path: str
    scene_order: int
    duration: Optional[float] = None
    
    class Config:
        from_attributes = True


class ProcessingStatus(BaseModel):
    status: str
    message: str
    parable_id: int


class ParableDetailResponse(ParableResponse):
    image_prompts: List[ImagePromptResponse] = []
    generated_images: List[GeneratedImageResponse] = []
    audio_files: List[AudioFileResponse] = []
    video_fragments: List[VideoFragmentResponse] = []
    
    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
# ENGLISH VERSION SCHEMAS
# ═══════════════════════════════════════════════════════════════

class EnglishParableResponse(BaseModel):
    id: int
    parable_id: int
    created_at: datetime
    text_for_tts: Optional[str] = None
    youtube_title: Optional[str] = None
    youtube_description: Optional[str] = None
    youtube_hashtags: Optional[str] = None
    status: str
    current_step: Optional[int] = 0
    error_message: Optional[str] = None
    final_video_path: Optional[str] = None
    final_video_duration: Optional[float] = None
    
    class Config:
        from_attributes = True


class EnglishImagePromptResponse(BaseModel):
    id: int
    english_parable_id: int
    prompt_text: str
    scene_order: int
    
    class Config:
        from_attributes = True


class EnglishGeneratedImageResponse(BaseModel):
    id: int
    english_parable_id: int
    prompt_id: int
    image_path: str
    scene_order: int
    
    class Config:
        from_attributes = True


class EnglishAudioFileResponse(BaseModel):
    id: int
    english_parable_id: int
    audio_path: str
    duration: Optional[float] = None
    
    class Config:
        from_attributes = True


class EnglishVideoFragmentResponse(BaseModel):
    id: int
    english_parable_id: int
    image_id: Optional[int] = None
    video_path: str
    scene_order: int
    duration: Optional[float] = None
    
    class Config:
        from_attributes = True


class EnglishParableDetailResponse(EnglishParableResponse):
    image_prompts: List[EnglishImagePromptResponse] = []
    generated_images: List[EnglishGeneratedImageResponse] = []
    audio_files: List[EnglishAudioFileResponse] = []
    video_fragments: List[EnglishVideoFragmentResponse] = []
    
    class Config:
        from_attributes = True

