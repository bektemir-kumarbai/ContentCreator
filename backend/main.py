from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
import shutil
from pathlib import Path

from database import get_db, engine
from models import (
    Base, Parable, ImagePrompt, GeneratedImage, AudioFile, VideoFragment,
    EnglishParable, EnglishImagePrompt, EnglishGeneratedImage, EnglishAudioFile, EnglishVideoFragment
)
from schemas import (
    ParableCreate, ParableResponse, ParableDetailResponse,
    ProcessingStatus, VideoFragmentResponse,
    EnglishParableResponse, EnglishParableDetailResponse, EnglishVideoFragmentResponse
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
    Если статус 'error', возобновляет с места остановки
    """
    parable = db.query(Parable).filter(Parable.id == parable_id).first()
    if not parable:
        raise HTTPException(status_code=404, detail="Parable not found")
    
    if parable.status == "processing":
        raise HTTPException(status_code=400, detail="Parable is already being processed")
    
    # Определяем, это новая обработка или возобновление
    is_resume = parable.status == "error"
    
    # Обновляем статус
    parable.status = "processing"
    # Не сбрасываем current_step если это возобновление
    if not is_resume:
        parable.current_step = 0
        parable.error_message = None
    
    db.commit()
    
    # Запускаем обработку в фоне
    background_tasks.add_task(process_parable_pipeline, parable_id, db)
    
    message = "Parable processing resumed from step {}".format(parable.current_step) if is_resume else "Parable processing started"
    
    return ProcessingStatus(
        status="processing",
        message=message,
        parable_id=parable_id
    )


async def process_parable_pipeline(parable_id: int, db: Session):
    """
    Основной пайплайн обработки притчи с возможностью возобновления
    """
    try:
        parable = db.query(Parable).filter(Parable.id == parable_id).first()
        start_step = parable.current_step if parable.current_step else 0
        
        print(f"[Parable {parable_id}] Starting from step {start_step}")
        
        # Шаг 1: Переписываем текст для TTS
        if start_step <= 1:
            print(f"[Parable {parable_id}] Step 1: Rewriting text for TTS...")
            parable.current_step = 1
            parable.error_message = None
            db.commit()
            
            tts_text = await gemini_service.rewrite_for_tts(parable.text_original)
            parable.text_for_tts = tts_text
            db.commit()
            print(f"[Parable {parable_id}] ✅ Step 1 completed")
        else:
            print(f"[Parable {parable_id}] ⏭️  Step 1 already completed, skipping...")
            tts_text = parable.text_for_tts
        
        # Шаг 2: Генерируем метаданные и промпты
        if start_step <= 2:
            print(f"[Parable {parable_id}] Step 2: Generating metadata and prompts...")
            parable.current_step = 2
            db.commit()
            
            # Проверяем, есть ли уже промпты
            existing_prompts = db.query(ImagePrompt).filter(
                ImagePrompt.parable_id == parable_id
            ).count()
            
            if existing_prompts == 0:
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
            else:
                print(f"[Parable {parable_id}] Prompts already exist, using existing...")
            
            print(f"[Parable {parable_id}] ✅ Step 2 completed")
        else:
            print(f"[Parable {parable_id}] ⏭️  Step 2 already completed, skipping...")
        
        # Шаг 3: Генерируем изображения
        if start_step <= 3:
            print(f"[Parable {parable_id}] Step 3: Generating images...")
            parable.current_step = 3
            db.commit()
            
            # Получаем все промпты
            prompts = db.query(ImagePrompt).filter(
                ImagePrompt.parable_id == parable_id
            ).order_by(ImagePrompt.scene_order).all()
            
            if not prompts:
                raise Exception("No image prompts found. Please run step 2 first.")
            
            # Проверяем, сколько изображений уже есть
            existing_images_count = db.query(GeneratedImage).filter(
                GeneratedImage.parable_id == parable_id
            ).count()
            
            print(f"[Parable {parable_id}] Found {existing_images_count}/{len(prompts)} existing images")
            
            # Генерируем только если не все изображения готовы
            if existing_images_count < len(prompts):
                image_prompts = [p.prompt_text for p in prompts]
                image_paths = await gemini_service.generate_images_with_context(
                    image_prompts,
                    parable_id
                )
                
                # Удаляем старые записи из БД (если были частично сгенерированы)
                db.query(GeneratedImage).filter(
                    GeneratedImage.parable_id == parable_id
                ).delete()
                db.commit()
                
                # Сохраняем ВСЕ изображения в БД заново
                saved_count = 0
                for idx, image_path in enumerate(image_paths):
                    if image_path:  # Проверяем что изображение действительно есть
                        image = GeneratedImage(
                            parable_id=parable_id,
                            prompt_id=prompts[idx].id,
                            image_path=image_path,
                            scene_order=idx
                        )
                        db.add(image)
                        saved_count += 1
                db.commit()
                
                print(f"[Parable {parable_id}] Saved {saved_count}/{len(prompts)} images to database")
                
                # Проверяем что ВСЕ изображения сгенерированы
                if saved_count < len(prompts):
                    raise Exception(f"Only {saved_count}/{len(prompts)} images were generated. Please retry.")
            else:
                print(f"[Parable {parable_id}] All images already exist, using existing...")
            
            # Финальная проверка
            final_count = db.query(GeneratedImage).filter(
                GeneratedImage.parable_id == parable_id
            ).count()
            
            if final_count < len(prompts):
                raise Exception(f"Image generation incomplete: {final_count}/{len(prompts)} images. Please retry step 3.")
            
            print(f"[Parable {parable_id}] ✅ Step 3 completed: {final_count}/{len(prompts)} images")
        else:
            print(f"[Parable {parable_id}] ⏭️  Step 3 already completed, skipping...")
            
            # Даже если пропускаем, проверяем что изображения есть
            prompts_count = db.query(ImagePrompt).filter(
                ImagePrompt.parable_id == parable_id
            ).count()
            images_count = db.query(GeneratedImage).filter(
                GeneratedImage.parable_id == parable_id
            ).count()
            
            if images_count < prompts_count:
                print(f"[Parable {parable_id}] ⚠️  Warning: Only {images_count}/{prompts_count} images found!")
                print(f"[Parable {parable_id}] Re-running step 3...")
                parable.current_step = 3
                db.commit()
                # Рекурсивно вызываем этот же блок
                return await process_parable_pipeline(parable_id, db)
        
        # Шаг 4: Аудио (пользователь загружает вручную)
        if start_step <= 4:
            print(f"[Parable {parable_id}] Step 4: Audio (manual upload)...")
            parable.current_step = 4
            db.commit()
            
            # Проверяем, есть ли уже аудио
            existing_audio = db.query(AudioFile).filter(
                AudioFile.parable_id == parable_id
            ).first()
            
            if existing_audio:
                print(f"[Parable {parable_id}] ✅ Audio already uploaded")
            else:
                print(f"[Parable {parable_id}] ⏸️  Waiting for manual audio upload...")
            
            print(f"[Parable {parable_id}] ✅ Step 4 completed (TTS text prepared)")
        else:
            print(f"[Parable {parable_id}] ⏭️  Step 4 already completed, skipping...")
        
        # Финальная проверка перед завершением
        print(f"[Parable {parable_id}] Running final checks...")
        
        # Проверяем что все данные на месте
        prompts_count = db.query(ImagePrompt).filter(
            ImagePrompt.parable_id == parable_id
        ).count()
        images_count = db.query(GeneratedImage).filter(
            GeneratedImage.parable_id == parable_id
        ).count()
        audio_count = db.query(AudioFile).filter(
            AudioFile.parable_id == parable_id
        ).count()
        
        print(f"[Parable {parable_id}] Final check results:")
        print(f"  - TTS text: {'✅' if parable.text_for_tts else '❌'}")
        print(f"  - Prompts: {prompts_count} {'✅' if prompts_count > 0 else '❌'}")
        print(f"  - Images: {images_count}/{prompts_count} {'✅' if images_count == prompts_count else '❌'}")
        print(f"  - Audio: {audio_count} {'⏸️  Manual upload required' if audio_count == 0 else '✅'}")
        
        # Проверяем критичные данные
        if not parable.text_for_tts:
            raise Exception("TTS text is missing!")
        if prompts_count == 0:
            raise Exception("No image prompts found!")
        if images_count < prompts_count:
            raise Exception(f"Images incomplete: {images_count}/{prompts_count}. Please retry step 3.")
        
        # Аудио теперь загружается вручную, не требуем его сразу
        # Обновляем статус
        parable.status = "awaiting_audio"
        parable.current_step = 5
        parable.error_message = None
        db.commit()
        
        print(f"[Parable {parable_id}] ✅ Processing completed!")
        print(f"[Parable {parable_id}] ⏸️  Please upload audio file manually.")
        print(f"[Parable {parable_id}] 📝 TTS text is ready for voice-over.")
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[Parable {parable_id}] ❌ Error at step {parable.current_step}: {str(e)}")
        print(error_details)
        
        parable = db.query(Parable).filter(Parable.id == parable_id).first()
        parable.status = "error"
        parable.error_message = f"Step {parable.current_step}: {str(e)}"
        db.commit()


@app.post("/parables/{parable_id}/audio/upload")
async def upload_audio(
    parable_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Загружает аудиофайл для притчи
    """
    parable = db.query(Parable).filter(Parable.id == parable_id).first()
    if not parable:
        raise HTTPException(status_code=404, detail="Parable not found")
    
    # Проверяем формат файла
    if not file.filename.endswith(('.mp3', '.wav', '.m4a')):
        raise HTTPException(status_code=400, detail="Only audio files (.mp3, .wav, .m4a) are allowed")
    
    # Сохраняем аудио
    audio_dir = settings.upload_dir / "audio" / str(parable_id)
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_path = audio_dir / "narration.mp3"
    
    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Получаем длительность аудио
    from pydub import AudioSegment
    audio_segment = AudioSegment.from_file(str(audio_path))
    duration = len(audio_segment) / 1000.0  # в секундах
    
    # Удаляем старое аудио если есть
    existing_audio = db.query(AudioFile).filter(
        AudioFile.parable_id == parable_id
    ).first()
    if existing_audio:
        db.delete(existing_audio)
    
    # Сохраняем в БД
    audio_file = AudioFile(
        parable_id=parable_id,
        audio_path=str(audio_path),
        duration=duration
    )
    db.add(audio_file)
    
    # Статус не меняем - можно загружать аудио в любой момент
    db.commit()
    db.refresh(audio_file)
    
    print(f"[Parable {parable_id}] ✅ Audio uploaded: {audio_path} ({duration:.2f}s)")
    
    return audio_file


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


@app.post("/parables/{parable_id}/regenerate-images", response_model=ProcessingStatus)
async def regenerate_images(
    parable_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Принудительно перегенерирует изображения для притчи
    """
    parable = db.query(Parable).filter(Parable.id == parable_id).first()
    if not parable:
        raise HTTPException(status_code=404, detail="Parable not found")
    
    # Проверяем что есть промпты
    prompts_count = db.query(ImagePrompt).filter(
        ImagePrompt.parable_id == parable_id
    ).count()
    
    if prompts_count == 0:
        raise HTTPException(status_code=400, detail="No image prompts found. Please run processing first.")
    
    # Запускаем генерацию в фоне
    background_tasks.add_task(regenerate_images_task, parable_id, db)
    
    return ProcessingStatus(
        status="processing",
        message=f"Image regeneration started for {prompts_count} scenes",
        parable_id=parable_id
    )


async def regenerate_images_task(parable_id: int, db: Session):
    """
    Задача перегенерации изображений
    """
    try:
        parable = db.query(Parable).filter(Parable.id == parable_id).first()
        
        print(f"[Parable {parable_id}] Starting image regeneration...")
        
        # Получаем промпты
        prompts = db.query(ImagePrompt).filter(
            ImagePrompt.parable_id == parable_id
        ).order_by(ImagePrompt.scene_order).all()
        
        if not prompts:
            print(f"[Parable {parable_id}] ❌ No prompts found")
            return
        
        # Генерируем изображения
        image_prompts = [p.prompt_text for p in prompts]
        image_paths = await gemini_service.generate_images_with_context(
            image_prompts,
            parable_id
        )
        
        # Удаляем старые записи из БД
        db.query(GeneratedImage).filter(
            GeneratedImage.parable_id == parable_id
        ).delete()
        db.commit()
        
        # Сохраняем новые изображения
        saved_count = 0
        for idx, image_path in enumerate(image_paths):
            if image_path:
                image = GeneratedImage(
                    parable_id=parable_id,
                    prompt_id=prompts[idx].id,
                    image_path=image_path,
                    scene_order=idx
                )
                db.add(image)
                saved_count += 1
        db.commit()
        
        print(f"[Parable {parable_id}] ✅ Image regeneration completed: {saved_count}/{len(prompts)} images")
        
        # Обновляем current_step если нужно
        if saved_count == len(prompts) and parable.current_step < 4:
            parable.current_step = 3
            db.commit()
        
    except Exception as e:
        print(f"[Parable {parable_id}] ❌ Error regenerating images: {str(e)}")


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
        parable.final_video_duration = float(duration)  # Конвертируем numpy.float64 в Python float
        parable.status = "completed"
        db.commit()
        
        print(f"[Parable {parable_id}] Final video generated: {final_path}")
        
    except Exception as e:
        print(f"[Parable {parable_id}] Error generating final video: {str(e)}")
        db.rollback()  # Откатываем неудачную транзакцию
        parable = db.query(Parable).filter(Parable.id == parable_id).first()
        if parable:
            parable.status = "error"
            parable.error_message = str(e)
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


# ═══════════════════════════════════════════════════════════════
# ENGLISH VERSION ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.post("/parables/{parable_id}/english/create", response_model=EnglishParableResponse)
async def create_english_version(
    parable_id: int,
    db: Session = Depends(get_db)
):
    """
    Создаёт английскую версию притчи
    """
    # Проверяем существование оригинальной притчи
    parable = db.query(Parable).filter(Parable.id == parable_id).first()
    if not parable:
        raise HTTPException(status_code=404, detail="Parable not found")
    
    # Проверяем что оригинал обработан
    if not parable.text_for_tts:
        raise HTTPException(status_code=400, detail="Original parable must be processed first")
    
    # Проверяем что английская версия ещё не создана
    existing = db.query(EnglishParable).filter(EnglishParable.parable_id == parable_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="English version already exists")
    
    # Создаём английскую версию
    english_parable = EnglishParable(
        parable_id=parable_id,
        status="draft"
    )
    db.add(english_parable)
    db.commit()
    db.refresh(english_parable)
    
    return english_parable


@app.get("/parables/{parable_id}/english", response_model=EnglishParableDetailResponse)
async def get_english_version(
    parable_id: int,
    db: Session = Depends(get_db)
):
    """
    Получает английскую версию притчи
    """
    english_parable = db.query(EnglishParable).filter(
        EnglishParable.parable_id == parable_id
    ).first()
    
    if not english_parable:
        raise HTTPException(status_code=404, detail="English version not found")
    
    return english_parable


@app.post("/parables/{parable_id}/english/process", response_model=ProcessingStatus)
async def process_english_version(
    parable_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Запускает обработку английской версии
    """
    # Проверяем существование оригинальной притчи
    parable = db.query(Parable).filter(Parable.id == parable_id).first()
    if not parable:
        raise HTTPException(status_code=404, detail="Parable not found")
    
    # Проверяем существование английской версии
    english_parable = db.query(EnglishParable).filter(
        EnglishParable.parable_id == parable_id
    ).first()
    
    if not english_parable:
        raise HTTPException(status_code=404, detail="English version not found. Create it first.")
    
    # Запускаем обработку в фоне
    background_tasks.add_task(process_english_parable_pipeline, english_parable.id, parable_id, db)
    
    return ProcessingStatus(
        status="processing",
        message="English version processing started",
        parable_id=english_parable.id
    )


async def process_english_parable_pipeline(english_parable_id: int, original_parable_id: int, db: Session):
    """
    Пайплайн обработки английской версии притчи
    """
    try:
        english_parable = db.query(EnglishParable).filter(EnglishParable.id == english_parable_id).first()
        parable = db.query(Parable).filter(Parable.id == original_parable_id).first()
        
        english_parable.status = "processing"
        db.commit()
        
        start_step = english_parable.current_step
        
        # Шаг 1: Переводим текст для TTS
        if start_step <= 1:
            print(f"[English Parable {english_parable_id}] Step 1: Translating text for TTS...")
            english_parable.current_step = 1
            db.commit()
            
            english_tts_text = await gemini_service.translate_to_english_for_tts(parable.text_for_tts)
            english_parable.text_for_tts = english_tts_text
            db.commit()
            
            print(f"[English Parable {english_parable_id}] ✅ Step 1 completed")
        else:
            print(f"[English Parable {english_parable_id}] ⏭️  Step 1 already completed, skipping...")
        
        # Шаг 2: Генерируем метаданные и промпты
        if start_step <= 2:
            print(f"[English Parable {english_parable_id}] Step 2: Generating metadata and prompts...")
            english_parable.current_step = 2
            db.commit()
            
            metadata = await gemini_service.generate_english_metadata_and_prompts(
                parable.text_for_tts,
                english_parable.text_for_tts
            )
            
            english_parable.youtube_title = metadata.get("youtube_title")
            english_parable.youtube_description = metadata.get("youtube_description")
            english_parable.youtube_hashtags = metadata.get("youtube_hashtags")
            db.commit()
            
            # Сохраняем промпты
            for idx, prompt_text in enumerate(metadata.get("image_prompts", [])):
                prompt = EnglishImagePrompt(
                    english_parable_id=english_parable_id,
                    prompt_text=prompt_text,
                    scene_order=idx
                )
                db.add(prompt)
            db.commit()
            
            print(f"[English Parable {english_parable_id}] ✅ Step 2 completed")
        else:
            print(f"[English Parable {english_parable_id}] ⏭️  Step 2 already completed, skipping...")
        
        # Шаг 3: Генерируем изображения
        if start_step <= 3:
            print(f"[English Parable {english_parable_id}] Step 3: Generating images...")
            english_parable.current_step = 3
            db.commit()
            
            prompts = db.query(EnglishImagePrompt).filter(
                EnglishImagePrompt.english_parable_id == english_parable_id
            ).order_by(EnglishImagePrompt.scene_order).all()
            prompts_count = len(prompts)
            
            existing_images_count = db.query(EnglishGeneratedImage).filter(
                EnglishGeneratedImage.english_parable_id == english_parable_id
            ).count()
            
            if existing_images_count < prompts_count:
                print(f"[English Parable {english_parable_id}] Need to generate {prompts_count - existing_images_count} images.")
                image_prompts = [p.prompt_text for p in prompts]
                # Используем специальную папку для английских изображений
                image_paths = await gemini_service.generate_images_with_context(
                    image_prompts,
                    f"english_{english_parable_id}"
                )
                
                for idx, image_path in enumerate(image_paths):
                    existing_image_db = db.query(EnglishGeneratedImage).filter(
                        EnglishGeneratedImage.english_parable_id == english_parable_id,
                        EnglishGeneratedImage.scene_order == idx
                    ).first()
                    
                    if not existing_image_db:
                        prompt_obj = next((p for p in prompts if p.scene_order == idx), None)
                        if prompt_obj:
                            image = EnglishGeneratedImage(
                                english_parable_id=english_parable_id,
                                prompt_id=prompt_obj.id,
                                image_path=image_path,
                                scene_order=idx
                            )
                            db.add(image)
                db.commit()
            else:
                print(f"[English Parable {english_parable_id}] All {prompts_count} images already exist, skipping generation.")
            
            saved_count = db.query(EnglishGeneratedImage).filter(
                EnglishGeneratedImage.english_parable_id == english_parable_id
            ).count()
            
            if saved_count < prompts_count:
                raise Exception(f"Only {saved_count}/{prompts_count} images generated. Please retry.")
            
            print(f"[English Parable {english_parable_id}] ✅ Step 3 completed: {saved_count}/{prompts_count} images")
        else:
            print(f"[English Parable {english_parable_id}] ⏭️  Step 3 already completed, skipping...")
        
        # Шаг 4: Аудио (ручная загрузка)
        if start_step <= 4:
            print(f"[English Parable {english_parable_id}] Step 4: Audio (manual upload)...")
            english_parable.current_step = 4
            db.commit()
            
            existing_audio = db.query(EnglishAudioFile).filter(
                EnglishAudioFile.english_parable_id == english_parable_id
            ).first()
            
            if existing_audio:
                print(f"[English Parable {english_parable_id}] ✅ Audio already uploaded")
            else:
                print(f"[English Parable {english_parable_id}] ⏸️  Waiting for manual audio upload...")
            
            print(f"[English Parable {english_parable_id}] ✅ Step 4 completed (TTS text prepared)")
        else:
            print(f"[English Parable {english_parable_id}] ⏭️  Step 4 already completed, skipping...")
        
        # Финальная проверка
        print(f"[English Parable {english_parable_id}] Running final checks...")
        
        prompts_count = db.query(EnglishImagePrompt).filter(
            EnglishImagePrompt.english_parable_id == english_parable_id
        ).count()
        images_count = db.query(EnglishGeneratedImage).filter(
            EnglishGeneratedImage.english_parable_id == english_parable_id
        ).count()
        
        print(f"[English Parable {english_parable_id}] Final check results:")
        print(f"  - TTS text: {'✅' if english_parable.text_for_tts else '❌'}")
        print(f"  - Prompts: {prompts_count} {'✅' if prompts_count > 0 else '❌'}")
        print(f"  - Images: {images_count}/{prompts_count} {'✅' if images_count == prompts_count else '❌'}")
        
        if not english_parable.text_for_tts:
            raise Exception("TTS text is missing!")
        if prompts_count == 0:
            raise Exception("No image prompts found!")
        if images_count < prompts_count:
            raise Exception(f"Images incomplete: {images_count}/{prompts_count}. Please retry step 3.")
        
        english_parable.status = "awaiting_audio"
        english_parable.current_step = 5
        english_parable.error_message = None
        db.commit()
        
        print(f"[English Parable {english_parable_id}] ✅ Processing completed!")
        print(f"[English Parable {english_parable_id}] ⏸️  Please upload audio file manually.")
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[English Parable {english_parable_id}] ❌ Error: {str(e)}")
        print(error_details)
        
        english_parable = db.query(EnglishParable).filter(EnglishParable.id == english_parable_id).first()
        if english_parable:
            english_parable.status = "error"
            english_parable.error_message = str(e)
            db.commit()


@app.post("/parables/{parable_id}/english/audio/upload")
async def upload_english_audio(
    parable_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Загружает аудиофайл для английской версии
    """
    english_parable = db.query(EnglishParable).filter(
        EnglishParable.parable_id == parable_id
    ).first()
    
    if not english_parable:
        raise HTTPException(status_code=404, detail="English version not found")
    
    if not file.filename.endswith(('.mp3', '.wav', '.m4a')):
        raise HTTPException(status_code=400, detail="Only audio files (.mp3, .wav, .m4a) are allowed")
    
    audio_dir = settings.upload_dir / "audio" / f"english_{english_parable.id}"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_path = audio_dir / "narration.mp3"
    
    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    from pydub import AudioSegment
    audio_segment = AudioSegment.from_file(str(audio_path))
    duration = len(audio_segment) / 1000.0
    
    existing_audio = db.query(EnglishAudioFile).filter(
        EnglishAudioFile.english_parable_id == english_parable.id
    ).first()
    if existing_audio:
        db.delete(existing_audio)
    
    audio_file = EnglishAudioFile(
        english_parable_id=english_parable.id,
        audio_path=str(audio_path),
        duration=duration
    )
    db.add(audio_file)
    
    # Статус не меняем - можно загружать аудио в любой момент
    db.commit()
    db.refresh(audio_file)
    
    print(f"[English Parable {english_parable.id}] ✅ Audio uploaded: {audio_path} ({duration:.2f}s)")
    
    return audio_file


@app.post("/parables/{parable_id}/english/videos/upload")
async def upload_english_video_fragment(
    parable_id: int,
    scene_order: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Загружает видеофрагмент для английской версии
    """
    english_parable = db.query(EnglishParable).filter(
        EnglishParable.parable_id == parable_id
    ).first()
    
    if not english_parable:
        raise HTTPException(status_code=404, detail="English version not found")
    
    # Сохраняем видео
    video_dir = settings.upload_dir / "videos" / f"english_{english_parable.id}"
    video_dir.mkdir(parents=True, exist_ok=True)
    video_path = video_dir / f"scene_{scene_order}.mp4"
    
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Получаем длительность видео
    duration = await video_service.get_video_duration(str(video_path))
    
    # Получаем соответствующее изображение
    image = db.query(EnglishGeneratedImage).filter(
        EnglishGeneratedImage.english_parable_id == english_parable.id,
        EnglishGeneratedImage.scene_order == scene_order
    ).first()
    
    # Сохраняем в БД
    video_fragment = EnglishVideoFragment(
        english_parable_id=english_parable.id,
        image_id=image.id if image else None,
        video_path=str(video_path),
        scene_order=scene_order,
        duration=duration
    )
    db.add(video_fragment)
    db.commit()
    db.refresh(video_fragment)
    
    return video_fragment


@app.post("/parables/{parable_id}/english/generate-final", response_model=ProcessingStatus)
async def generate_english_final_video(
    parable_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Генерирует финальное видео для английской версии
    """
    english_parable = db.query(EnglishParable).filter(
        EnglishParable.parable_id == parable_id
    ).first()
    
    if not english_parable:
        raise HTTPException(status_code=404, detail="English version not found")
    
    # Проверяем наличие всех необходимых данных
    video_fragments = db.query(EnglishVideoFragment).filter(
        EnglishVideoFragment.english_parable_id == english_parable.id
    ).order_by(EnglishVideoFragment.scene_order).all()
    
    if not video_fragments:
        raise HTTPException(status_code=400, detail="No video fragments uploaded")
    
    audio_file = db.query(EnglishAudioFile).filter(
        EnglishAudioFile.english_parable_id == english_parable.id
    ).first()
    
    if not audio_file:
        raise HTTPException(status_code=400, detail="No audio file found")
    
    # Обновляем статус
    english_parable.status = "generating_final"
    db.commit()
    
    # Запускаем генерацию в фоне
    background_tasks.add_task(generate_english_final_video_task, english_parable.id, db)
    
    return ProcessingStatus(
        status="generating_final",
        message="English final video generation started",
        parable_id=english_parable.id
    )


async def generate_english_final_video_task(english_parable_id: int, db: Session):
    """
    Задача генерации финального видео для английской версии
    """
    try:
        english_parable = db.query(EnglishParable).filter(EnglishParable.id == english_parable_id).first()
        
        # Получаем все видеофрагменты
        video_fragments = db.query(EnglishVideoFragment).filter(
            EnglishVideoFragment.english_parable_id == english_parable_id
        ).order_by(EnglishVideoFragment.scene_order).all()
        
        video_paths = [vf.video_path for vf in video_fragments]
        
        # Получаем аудио
        audio_file = db.query(EnglishAudioFile).filter(
            EnglishAudioFile.english_parable_id == english_parable_id
        ).first()
        
        print(f"[English Parable {english_parable_id}] Generating final video...")
        
        # Создаём финальное видео
        final_path, duration = await video_service.create_final_video(
            video_paths=video_paths,
            audio_path=audio_file.audio_path,
            text_for_subtitles=english_parable.text_for_tts,
            parable_id=f"english_{english_parable_id}"
        )
        
        # Обновляем притчу
        english_parable.final_video_path = final_path
        english_parable.final_video_duration = float(duration)  # Конвертируем numpy.float64 в Python float
        english_parable.status = "completed"
        db.commit()
        
        print(f"[English Parable {english_parable_id}] Final video generated: {final_path}")
        
    except Exception as e:
        print(f"[English Parable {english_parable_id}] Error generating final video: {str(e)}")
        db.rollback()
        english_parable = db.query(EnglishParable).filter(EnglishParable.id == english_parable_id).first()
        if english_parable:
            english_parable.status = "error"
            english_parable.error_message = str(e)
            db.commit()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

