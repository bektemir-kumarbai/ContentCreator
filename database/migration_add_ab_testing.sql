-- Миграция: Система A/B тестирования заголовков

-- Таблица вариантов заголовков для русских притч
CREATE TABLE IF NOT EXISTS title_variants (
    id SERIAL PRIMARY KEY,
    parable_id INTEGER NOT NULL REFERENCES parables(id) ON DELETE CASCADE,
    variant_text TEXT NOT NULL,
    variant_type VARCHAR(50) NOT NULL, -- question, intrigue, emotion, numbers, provocation
    is_selected BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица вариантов заголовков для английских притч
CREATE TABLE IF NOT EXISTS english_title_variants (
    id SERIAL PRIMARY KEY,
    english_parable_id INTEGER NOT NULL REFERENCES english_parables(id) ON DELETE CASCADE,
    variant_text TEXT NOT NULL,
    variant_type VARCHAR(50) NOT NULL,
    is_selected BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы
CREATE INDEX idx_title_variants_parable ON title_variants(parable_id);
CREATE INDEX idx_english_title_variants_english ON english_title_variants(english_parable_id);
CREATE INDEX idx_title_variants_selected ON title_variants(is_selected);
CREATE INDEX idx_english_title_variants_selected ON english_title_variants(is_selected);

COMMENT ON TABLE title_variants IS 'Варианты заголовков для A/B тестирования';
COMMENT ON COLUMN title_variants.variant_type IS 'Тип заголовка: question (вопрос), intrigue (интрига), emotion (эмоция), numbers (с цифрами), provocation (провокация)';
COMMENT ON COLUMN title_variants.is_selected IS 'Выбран ли этот вариант пользователем';

