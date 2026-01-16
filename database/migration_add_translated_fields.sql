-- Миграция: добавление полей для переведённого заголовка и текста

ALTER TABLE english_parables 
ADD COLUMN IF NOT EXISTS title_translated TEXT;

ALTER TABLE english_parables 
ADD COLUMN IF NOT EXISTS text_translated TEXT;

