-- Миграция для добавления полей возобновления обработки
-- Дата: 2026-01-15

-- Добавляем поле current_step для отслеживания текущего шага
ALTER TABLE parables 
ADD COLUMN IF NOT EXISTS current_step INTEGER DEFAULT 0;

-- Добавляем поле error_message для хранения сообщения об ошибке
ALTER TABLE parables 
ADD COLUMN IF NOT EXISTS error_message TEXT;

-- Обновляем существующие записи
UPDATE parables 
SET current_step = 0 
WHERE current_step IS NULL;

-- Комментарии к полям
COMMENT ON COLUMN parables.current_step IS 'Текущий шаг обработки: 0-ожидание, 1-TTS, 2-метаданные, 3-изображения, 4-аудио, 5-завершено';
COMMENT ON COLUMN parables.error_message IS 'Сообщение об ошибке при обработке';


