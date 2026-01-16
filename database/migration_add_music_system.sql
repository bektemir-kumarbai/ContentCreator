-- Миграция: Система музыкального сопровождения

-- Таблица музыкальных треков
CREATE TABLE IF NOT EXISTS music_tracks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    file_path TEXT, -- Путь к файлу, может быть NULL для placeholder треков
    mood VARCHAR(50) NOT NULL, -- dramatic, calm, motivational, mystical, inspiring, sad, joyful
    duration FLOAT,
    bpm INTEGER,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Связь притчи с музыкой
CREATE TABLE IF NOT EXISTS parable_music (
    id SERIAL PRIMARY KEY,
    parable_id INTEGER NOT NULL REFERENCES parables(id) ON DELETE CASCADE,
    music_track_id INTEGER REFERENCES music_tracks(id) ON DELETE SET NULL,
    volume_level FLOAT DEFAULT -18.0, -- dB относительно голоса
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(parable_id)
);

-- Связь английской версии с музыкой
CREATE TABLE IF NOT EXISTS english_parable_music (
    id SERIAL PRIMARY KEY,
    english_parable_id INTEGER NOT NULL REFERENCES english_parables(id) ON DELETE CASCADE,
    music_track_id INTEGER REFERENCES music_tracks(id) ON DELETE SET NULL,
    volume_level FLOAT DEFAULT -18.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(english_parable_id)
);

-- Индексы
CREATE INDEX idx_music_tracks_mood ON music_tracks(mood);
CREATE INDEX idx_parable_music_parable ON parable_music(parable_id);
CREATE INDEX idx_english_parable_music_english ON english_parable_music(english_parable_id);

-- Добавляем несколько примеров треков (пути будут заполнены позже)
INSERT INTO music_tracks (name, mood, description) VALUES
('Epic Cinematic', 'dramatic', 'Драматичная эпическая музыка для серьёзных притч'),
('Peaceful Ambient', 'calm', 'Спокойная эмбиентная музыка для медитативных притч'),
('Uplifting Motivation', 'motivational', 'Мотивационная музыка с нарастающим темпом'),
('Mystical Journey', 'mystical', 'Мистическая музыка для загадочных притч'),
('Inspiring Hope', 'inspiring', 'Вдохновляющая музыка с позитивным настроением'),
('Melancholic Piano', 'sad', 'Грустная фортепианная музыка для трогательных притч'),
('Joyful Celebration', 'joyful', 'Радостная музыка для позитивных притч');

