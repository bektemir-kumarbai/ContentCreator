from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip, TextClip, CompositeVideoClip
from moviepy.video.fx.all import speedx
from moviepy.audio.fx.all import volumex
from pathlib import Path
from config import settings
from typing import List, Tuple, Optional, Dict
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont


class VideoService:
    
    async def create_final_video(
        self,
        video_paths: List[str],
        audio_path: str,
        text_for_subtitles: str,
        parable_id: int,
        music_path: Optional[str] = None,
        music_volume_db: float = -18.0
    ) -> Tuple[str, float]:
        """
        Создаёт финальное видео с синхронизацией аудио и музыкой
        
        Args:
            video_paths: Пути к видеофрагментам
            audio_path: Путь к аудио озвучки
            text_for_subtitles: Текст для субтитров (не используется пока)
            parable_id: ID притчи
            music_path: Путь к музыкальному треку (опционально)
            music_volume_db: Громкость музыки в dB относительно голоса (по умолчанию -18dB)
        """
        # Загружаем все видеофрагменты
        video_clips = [VideoFileClip(path) for path in video_paths]
        
        # Убираем звук из всех видео
        video_clips = [clip.without_audio() for clip in video_clips]
        
        # Объединяем видео
        combined_video = concatenate_videoclips(video_clips, method="compose")
        
        # Загружаем аудио озвучки
        voice_audio = AudioFileClip(audio_path)
        audio_duration = voice_audio.duration
        video_duration = combined_video.duration
        
        # Синхронизируем длительность видео и аудио
        if video_duration > audio_duration:
            # Видео длиннее — ускоряем
            speed_factor = video_duration / audio_duration
            combined_video = combined_video.fx(speedx, speed_factor)
        elif video_duration < audio_duration:
            # Видео короче — замедляем
            speed_factor = video_duration / audio_duration
            combined_video = combined_video.fx(speedx, speed_factor)
        
        # Создаём финальный аудио микс
        if music_path and Path(music_path).exists():
            print(f"[Video Service] Adding background music: {music_path}")
            
            # Загружаем музыку
            music_audio = AudioFileClip(music_path)
            
            # Подгоняем длительность музыки под видео
            if music_audio.duration < voice_audio.duration:
                # Если музыка короче, зацикливаем её
                loops_needed = int(voice_audio.duration / music_audio.duration) + 1
                from moviepy.audio.AudioClip import concatenate_audioclips
                music_audio = concatenate_audioclips([music_audio] * loops_needed)
            
            # Обрезаем музыку до длительности голоса
            music_audio = music_audio.subclip(0, voice_audio.duration)
            
            # Конвертируем dB в множитель громкости
            # -18dB означает примерно 0.125 (12.5%) от оригинальной громкости
            volume_multiplier = 10 ** (music_volume_db / 20)
            music_audio = music_audio.fx(volumex, volume_multiplier)
            
            print(f"[Video Service] Music volume: {music_volume_db}dB (multiplier: {volume_multiplier:.3f})")
            
            # Микшируем голос и музыку
            final_audio = CompositeAudioClip([voice_audio, music_audio])
            
            # Закрываем музыкальный клип
            music_audio.close()
        else:
            # Если музыки нет, используем только голос
            final_audio = voice_audio
        
        # Добавляем финальный аудио к видео
        final_video = combined_video.set_audio(final_audio)
        
        # Добавляем субтитры
        if text_for_subtitles:
            print(f"[Video Service] Adding subtitles...")
            try:
                final_video = self._add_subtitles(final_video, text_for_subtitles, audio_path)
            except Exception as e:
                print(f"[Video Service] Warning: Could not add subtitles: {e}")
        
        # Проверяем длительность
        if final_video.duration > 60:
            # Ускоряем до 60 секунд
            speed_factor = final_video.duration / 60
            final_video = final_video.fx(speedx, speed_factor)
        
        # Сохраняем финальное видео
        output_dir = settings.output_dir / "final"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"parable_{parable_id}_final.mp4"
        
        final_video.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            fps=30,
            preset='medium',
            bitrate='8000k'
        )
        
        # Закрываем все клипы
        for clip in video_clips:
            clip.close()
        voice_audio.close()
        if final_audio != voice_audio:
            final_audio.close()
        final_video.close()
        
        return str(output_path), final_video.duration
    
    def _add_subtitles(self, video, text: str, audio_path: str):
        """
        Добавляет субтитры к видео с умной разбивкой по словам
        Использует PIL вместо ImageMagick для избежания зависимостей
        """
        import re
        
        # Очищаем текст от тегов эмоций [] и кавычек
        clean_text = re.sub(r'\[.*?\]', '', text)  # Убираем [excited], [calm] и т.д.
        clean_text = clean_text.replace('"', '').replace("'", '')  # Убираем кавычки
        clean_text = clean_text.replace('\n', ' ')  # Убираем переносы строк
        clean_text = re.sub(r'\s+', ' ', clean_text)  # Убираем лишние пробелы
        
        # Разбиваем текст на части с учётом хука
        sentences = []
        all_words = clean_text.split()
        
        # Первые ~15-20 слов - это обычно хук (быстрая речь)
        hook_words_count = min(20, len(all_words) // 3)
        hook_words = all_words[:hook_words_count]
        main_words = all_words[hook_words_count:]
        
        # ДЛЯ ХУКА: по 1-2 слова (очень быстро)
        for i in range(0, len(hook_words), 2):
            part = ' '.join(hook_words[i:i+2])
            if part:
                sentences.append(('hook', part))
        
        # ДЛЯ ОСНОВНОГО ТЕКСТА: по 2-3 слова (нормально)
        for i in range(0, len(main_words), 3):
            part = ' '.join(main_words[i:i+3])
            if part:
                sentences.append(('main', part))
        
        # Рассчитываем время для каждого субтитра
        total_duration = video.duration
        
        # Хук занимает примерно первые 15% времени (быстрее читается)
        hook_duration = total_duration * 0.15
        main_duration = total_duration * 0.85
        
        hook_count = sum(1 for t, _ in sentences if t == 'hook')
        main_count = sum(1 for t, _ in sentences if t == 'main')
        
        subtitle_clips = []
        current_time = 0
        
        for sent_type, sentence in sentences:
            # Длительность зависит от типа (хук быстрее)
            if sent_type == 'hook' and hook_count > 0:
                duration = hook_duration / hook_count
            elif main_count > 0:
                duration = main_duration / main_count
            else:
                duration = 1.0
            
            # Создаём изображение с текстом
            img = self._create_subtitle_image(sentence, video.w, 150)
            
            # Создаём клип из изображения
            from moviepy.video.VideoClip import ImageClip
            txt_clip = ImageClip(img).set_duration(duration).set_position(('center', video.h - 180)).set_start(current_time)
            
            subtitle_clips.append(txt_clip)
            current_time += duration
        
        # Накладываем субтитры на видео
        final_video = CompositeVideoClip([video] + subtitle_clips)
        
        return final_video
    
    def _create_subtitle_image(self, text: str, width: int, height: int) -> np.ndarray:
        """
        Создаёт изображение субтитра используя PIL
        """
        
        # Создаём изображение с прозрачным фоном
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Пытаемся загрузить шрифт (маленький размер)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
            except:
                font = ImageFont.load_default()
        
        # Получаем размер текста
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Позиция текста (по центру)
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Рисуем чёрный фон под текстом (для контраста, меньший padding)
        padding = 15
        draw.rectangle([x - padding, y - padding, x + text_width + padding, y + text_height + padding], 
                      fill=(0, 0, 0, 200))
        
        # Рисуем белый текст с чёрной обводкой (тоньше обводка)
        # Обводка
        for adj_x in [-1, 0, 1]:
            for adj_y in [-1, 0, 1]:
                if adj_x != 0 or adj_y != 0:
                    draw.text((x + adj_x, y + adj_y), text, font=font, fill=(0, 0, 0, 255))
        # Основной текст
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
        
        # Конвертируем в numpy array
        return np.array(img)
    
    async def get_video_duration(self, video_path: str) -> float:
        """
        Получает длительность видео
        """
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.close()
        return duration

