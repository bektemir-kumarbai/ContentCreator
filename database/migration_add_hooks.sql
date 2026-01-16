-- Миграция: Добавление хуков (цепляющих начал) для первых 3 секунд

-- Добавляем поле hook_text для русских притч
ALTER TABLE parables 
ADD COLUMN IF NOT EXISTS hook_text TEXT;

-- Добавляем поле hook_text для английских притч
ALTER TABLE english_parables 
ADD COLUMN IF NOT EXISTS hook_text TEXT;

COMMENT ON COLUMN parables.hook_text IS 'Цепляющее начало для первых 3 секунд видео';
COMMENT ON COLUMN english_parables.hook_text IS 'Catchy hook for the first 3 seconds of video';

