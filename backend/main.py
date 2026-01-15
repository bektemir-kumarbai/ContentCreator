from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
import shutil
from pathlib import Path

from database import get_db, engine
from models import Base, Parable, ImagePrompt, GeneratedImage, AudioFile, VideoFragment
from schemas import (
    ParableCreate, ParableResponse, ParableDetailResponse,
    ProcessingStatus, VideoFragmentResponse
)
from services.gemini_service import GeminiService
from services.elevenlabs_service import ElevenLabsService
from services.video_service import VideoService
from config import settings

# Создаём таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Content Creator API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статические файлы
app.mount("/uploads", StaticFiles(directory=str(settings.upload_dir)), name="uploads")
app.mount("/outputs", StaticFiles(directory=str(settings.output_dir)), name="outputs")

# Сервисы
gemini_service = GeminiService()
elevenlabs_service = ElevenLabsService()
video_service = VideoService()


@app.get("/")
async def root():
    return {"message": "Content Creator API is running"}


@app.post("/parables", response_model=ParableResponse)
async def create_parable(parable: ParableCreate, db: Session = Depends(get_db)):
    """
    Создаёт новую притчу
    """
    db_parable = Parable(
        title_original=parable.title_original,
        text_original=parable.text_original,
        status="draft"
    )
    db.add(db_parable)
    db.commit()
    db.refresh(db_parable)
    return db_parable


@app.get("/parables", response_model=List[ParableResponse])
async def get_parables(db: Session = Depends(get_db)):
    """
    Получает список всех притч
    """
    parables = db.query(Parable).order_by(Parable.created_at.desc()).all()
    return parables


@app.get("/parables/{parable_id}", response_model=ParableDetailResponse)
async def get_parable(parable_id: int, db: Session = Depends(get_db)):
    """
    Получает детальную информацию о притче
    """
    parable = db.query(Parable).filter(Parable.id == parable_id).first()
    if not parable:
        raise HTTPException(status_code=404, detail="Parable not found")
    return parable


@app.post("/parables/{parable_id}/process", response_model=ProcessingStatus)
async def process_parable(
    parable_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Запускает обработку притчи (пайплайн)
    """
    parable = db.query(Parable).filter(Parable.id == parable_id).first()
    if not parable:
        raise HTTPException(status_code=404, detail="Parable not found")
    
    if parable.status == "processing":
        raise HTTPException(status_code=400, detail="Parable is already being processed")
    
    # Обновляем статус
    parable.status = "processing"
    db.commit()
    
    # Запускаем обработку в фоне
    background_tasks.add_task(process_parable_pipeline, parable_id, db)
    
    return ProcessingStatus(
        status="processing",
        message="Parable processing started",
        parable_id=parable_id
    )


async def process_parable_pipeline(parable_id: int, db: Session):
    """
    Основной пайплайн обработки притчи
    """
    try:
        parable = db.query(Parable).filter(Parable.id == parable_id).first()
        
        # Шаг 1: Переписываем текст для TTS
        print(f"[Parable {parable_id}] Step 1: Rewriting text for TTS...")
        tts_text = await gemini_service.rewrite_for_tts(parable.text_original)
        parable.text_for_tts = tts_text
        db.commit()
        
        # Шаг 2: Генерируем метаданные и промпты
        print(f"[Parable {parable_id}] Step 2: Generating metadata and prompts...")
        metadata = await gemini_service.generate_metadata_and_prompts(
            parable.text_original,
            tts_text
        )
        
        parable.youtube_title = metadata['youtube_title']
        parable.youtube_description = metadata['youtube_description']
        parable.youtube_hashtags = metadata['youtube_hashtags']
        db.commit()
        
        # Сохраняем промпты в БД
        for idx, prompt_text in enumerate(metadata['image_prompts']):
            prompt = ImagePrompt(
                parable_id=parable_id,
                prompt_text=prompt_text,
                scene_order=idx
            )
            db.add(prompt)
        db.commit()
        
        # Шаг 3: Генерируем изображения
        print(f"[Parable {parable_id}] Step 3: Generating images...")
        image_paths = await gemini_service.generate_images_with_context(
            metadata['image_prompts'],
            parable_id
        )
        
        # Сохраняем изображения в БД
        prompts = db.query(ImagePrompt).filter(
            ImagePrompt.parable_id == parable_id
        ).order_by(ImagePrompt.scene_order).all()
        
        for idx, (image_path, prompt) in enumerate(zip(image_paths, prompts)):
            image = GeneratedImage(
                parable_id=parable_id,
                prompt_id=prompt.id,
                image_path=image_path,
                scene_order=idx
            )
            db.add(image)
        db.commit()
        
        # Шаг 4: Генерируем аудио
        print(f"[Parable {parable_id}] Step 4: Generating audio...")
        audio_path, duration = await elevenlabs_service.generate_audio(tts_text, parable_id)
        
        audio_file = AudioFile(
            parable_id=parable_id,
            audio_path=audio_path,
            duration=duration
        )
        db.add(audio_file)
        db.commit()
        
        # Обновляем статус
        parable.status = "awaiting_videos"
        db.commit()
        
        print(f"[Parable {parable_id}] Processing completed! Awaiting video uploads.")
        
    except Exception as e:
        print(f"[Parable {parable_id}] Error: {str(e)}")
        parable = db.query(Parable).filter(Parable.id == parable_id).first()
        parable.status = "error"
        db.commit()


@app.post("/parables/{parable_id}/videos/upload")
async def upload_video_fragment(
    parable_id: int,
    scene_order: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Загружает видеофрагмент для определённой сцены
    """
    parable = db.query(Parable).filter(Parable.id == parable_id).first()
    if not parable:
        raise HTTPException(status_code=404, detail="Parable not found")
    
    # Сохраняем видео
    video_dir = settings.upload_dir / "videos" / str(parable_id)
    video_dir.mkdir(parents=True, exist_ok=True)
    video_path = video_dir / f"scene_{scene_order}.mp4"
    
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Получаем длительность видео
    duration = await video_service.get_video_duration(str(video_path))
    
    # Получаем соответствующее изображение
    image = db.query(GeneratedImage).filter(
        GeneratedImage.parable_id == parable_id,
        GeneratedImage.scene_order == scene_order
    ).first()
    
    # Сохраняем в БД
    video_fragment = VideoFragment(
        parable_id=parable_id,
        image_id=image.id if image else None,
        video_path=str(video_path),
        scene_order=scene_order,
        duration=duration
    )
    db.add(video_fragment)
    db.commit()
    db.refresh(video_fragment)
    
    return video_fragment


@app.post("/parables/{parable_id}/generate-final", response_model=ProcessingStatus)
async def generate_final_video(
    parable_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Генерирует финальное видео
    """
    parable = db.query(Parable).filter(Parable.id == parable_id).first()
    if not parable:
        raise HTTPException(status_code=404, detail="Parable not found")
    
    # Проверяем наличие всех необходимых данных
    video_fragments = db.query(VideoFragment).filter(
        VideoFragment.parable_id == parable_id
    ).order_by(VideoFragment.scene_order).all()
    
    if not video_fragments:
        raise HTTPException(status_code=400, detail="No video fragments uploaded")
    
    audio_file = db.query(AudioFile).filter(
        AudioFile.parable_id == parable_id
    ).first()
    
    if not audio_file:
        raise HTTPException(status_code=400, detail="No audio file found")
    
    # Обновляем статус
    parable.status = "generating_final"
    db.commit()
    
    # Запускаем генерацию в фоне
    background_tasks.add_task(generate_final_video_task, parable_id, db)
    
    return ProcessingStatus(
        status="generating_final",
        message="Final video generation started",
        parable_id=parable_id
    )


async def generate_final_video_task(parable_id: int, db: Session):
    """
    Задача генерации финального видео
    """
    try:
        parable = db.query(Parable).filter(Parable.id == parable_id).first()
        
        # Получаем все видеофрагменты
        video_fragments = db.query(VideoFragment).filter(
            VideoFragment.parable_id == parable_id
        ).order_by(VideoFragment.scene_order).all()
        
        video_paths = [vf.video_path for vf in video_fragments]
        
        # Получаем аудио
        audio_file = db.query(AudioFile).filter(
            AudioFile.parable_id == parable_id
        ).first()
        
        print(f"[Parable {parable_id}] Generating final video...")
        
        # Создаём финальное видео
        final_path, duration = await video_service.create_final_video(
            video_paths=video_paths,
            audio_path=audio_file.audio_path,
            text_for_subtitles=parable.text_for_tts,
            parable_id=parable_id
        )
        
        # Обновляем притчу
        parable.final_video_path = final_path
        parable.final_video_duration = duration
        parable.status = "completed"
        db.commit()
        
        print(f"[Parable {parable_id}] Final video generated: {final_path}")
        
    except Exception as e:
        print(f"[Parable {parable_id}] Error generating final video: {str(e)}")
        parable = db.query(Parable).filter(Parable.id == parable_id).first()
        parable.status = "error"
        db.commit()


@app.delete("/parables/{parable_id}")
async def delete_parable(parable_id: int, db: Session = Depends(get_db)):
    """
    Удаляет притчу и все связанные файлы
    """
    parable = db.query(Parable).filter(Parable.id == parable_id).first()
    if not parable:
        raise HTTPException(status_code=404, detail="Parable not found")
    
    # Удаляем файлы
    image_dir = settings.upload_dir / "images" / str(parable_id)
    audio_dir = settings.upload_dir / "audio" / str(parable_id)
    video_dir = settings.upload_dir / "videos" / str(parable_id)
    
    for directory in [image_dir, audio_dir, video_dir]:
        if directory.exists():
            shutil.rmtree(directory)
    
    # Удаляем из БД (каскадно удалятся все связанные записи)
    db.delete(parable)
    db.commit()
    
    return {"message": "Parable deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

