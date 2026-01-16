-- Миграция: добавление поля video_prompt_text в таблицы промптов

-- Для основной таблицы промптов
ALTER TABLE image_prompts 
ADD COLUMN IF NOT EXISTS video_prompt_text TEXT NOT NULL DEFAULT '';

-- Для английской версии
ALTER TABLE english_image_prompts 
ADD COLUMN IF NOT EXISTS video_prompt_text TEXT NOT NULL DEFAULT '';

-- Обновляем существующие записи (если нужно)
UPDATE image_prompts SET video_prompt_text = '' WHERE video_prompt_text IS NULL;
UPDATE english_image_prompts SET video_prompt_text = '' WHERE video_prompt_text IS NULL;

