-- ═══════════════════════════════════════════════════════════════
-- МИГРАЦИЯ: ДОБАВЛЕНИЕ ТАБЛИЦ ДЛЯ АНГЛИЙСКОГО КОНТЕНТА
-- ═══════════════════════════════════════════════════════════════

-- Таблица английских притч
CREATE TABLE IF NOT EXISTS english_parables (
    id SERIAL PRIMARY KEY,
    parable_id INTEGER NOT NULL UNIQUE REFERENCES parables(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Переведённые данные
    text_for_tts TEXT,
    youtube_title TEXT,
    youtube_description TEXT,
    youtube_hashtags TEXT,
    
    -- Метаданные
    processed_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'draft',
    current_step INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- Финальное видео
    final_video_path TEXT,
    final_video_duration FLOAT,
    completed_at TIMESTAMP
);

-- Таблица промптов для английских изображений
CREATE TABLE IF NOT EXISTS english_image_prompts (
    id SERIAL PRIMARY KEY,
    english_parable_id INTEGER NOT NULL REFERENCES english_parables(id) ON DELETE CASCADE,
    prompt_text TEXT NOT NULL,
    scene_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица сгенерированных английских изображений
CREATE TABLE IF NOT EXISTS english_generated_images (
    id SERIAL PRIMARY KEY,
    english_parable_id INTEGER NOT NULL REFERENCES english_parables(id) ON DELETE CASCADE,
    prompt_id INTEGER NOT NULL REFERENCES english_image_prompts(id) ON DELETE CASCADE,
    image_path TEXT NOT NULL,
    scene_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица английских аудиофайлов
CREATE TABLE IF NOT EXISTS english_audio_files (
    id SERIAL PRIMARY KEY,
    english_parable_id INTEGER NOT NULL REFERENCES english_parables(id) ON DELETE CASCADE,
    audio_path TEXT NOT NULL,
    duration FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица английских видеофрагментов
CREATE TABLE IF NOT EXISTS english_video_fragments (
    id SERIAL PRIMARY KEY,
    english_parable_id INTEGER NOT NULL REFERENCES english_parables(id) ON DELETE CASCADE,
    image_id INTEGER REFERENCES english_generated_images(id) ON DELETE SET NULL,
    video_path TEXT NOT NULL,
    scene_order INTEGER NOT NULL,
    duration FLOAT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_english_parables_parable_id ON english_parables(parable_id);
CREATE INDEX IF NOT EXISTS idx_english_parables_status ON english_parables(status);
CREATE INDEX IF NOT EXISTS idx_english_image_prompts_parable_id ON english_image_prompts(english_parable_id);
CREATE INDEX IF NOT EXISTS idx_english_generated_images_parable_id ON english_generated_images(english_parable_id);
CREATE INDEX IF NOT EXISTS idx_english_audio_files_parable_id ON english_audio_files(english_parable_id);
CREATE INDEX IF NOT EXISTS idx_english_video_fragments_parable_id ON english_video_fragments(english_parable_id);

-- ═══════════════════════════════════════════════════════════════
-- ПРИМЕНЕНИЕ МИГРАЦИИ
-- ═══════════════════════════════════════════════════════════════

-- docker exec -i contentcreator_postgres psql -U admin -d contentcreator < database/migration_add_english_tables.sql


