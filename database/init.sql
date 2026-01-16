-- Таблица притч
CREATE TABLE IF NOT EXISTS parables (
    id SERIAL PRIMARY KEY,
    title_original TEXT NOT NULL,
    text_original TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Обработанные данные от Gemini
    text_for_tts TEXT,
    youtube_title TEXT,
    youtube_description TEXT,
    youtube_hashtags TEXT,
    
    -- Метаданные обработки
    processed_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'draft',
    
    -- Финальное видео
    final_video_path TEXT,
    final_video_duration FLOAT,
    completed_at TIMESTAMP
);

-- Таблица промптов для изображений
CREATE TABLE IF NOT EXISTS image_prompts (
    id SERIAL PRIMARY KEY,
    parable_id INTEGER NOT NULL REFERENCES parables(id) ON DELETE CASCADE,
    prompt_text TEXT NOT NULL,
    video_prompt_text TEXT NOT NULL,
    scene_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица сгенерированных изображений
CREATE TABLE IF NOT EXISTS generated_images (
    id SERIAL PRIMARY KEY,
    parable_id INTEGER NOT NULL REFERENCES parables(id) ON DELETE CASCADE,
    prompt_id INTEGER NOT NULL REFERENCES image_prompts(id) ON DELETE CASCADE,
    image_path TEXT NOT NULL,
    scene_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица аудио
CREATE TABLE IF NOT EXISTS audio_files (
    id SERIAL PRIMARY KEY,
    parable_id INTEGER NOT NULL REFERENCES parables(id) ON DELETE CASCADE,
    audio_path TEXT NOT NULL,
    duration FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица загруженных видеофрагментов (от Grok)
CREATE TABLE IF NOT EXISTS video_fragments (
    id SERIAL PRIMARY KEY,
    parable_id INTEGER NOT NULL REFERENCES parables(id) ON DELETE CASCADE,
    image_id INTEGER REFERENCES generated_images(id) ON DELETE SET NULL,
    video_path TEXT NOT NULL,
    scene_order INTEGER NOT NULL,
    duration FLOAT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для оптимизации
CREATE INDEX idx_parables_status ON parables(status);
CREATE INDEX idx_image_prompts_parable ON image_prompts(parable_id);
CREATE INDEX idx_generated_images_parable ON generated_images(parable_id);
CREATE INDEX idx_video_fragments_parable ON video_fragments(parable_id);

