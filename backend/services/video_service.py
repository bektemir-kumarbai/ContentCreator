from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
from moviepy.video.fx.all import speedx
from pathlib import Path
from config import settings
from typing import List, Tuple
import re


class VideoService:
    
    async def create_final_video(
        self,
        video_paths: List[str],
        audio_path: str,
        text_for_subtitles: str,
        parable_id: int
    ) -> Tuple[str, float]:
        """
        Создаёт финальное видео с синхронизацией аудио и субтитрами
        """
        # Загружаем все видеофрагменты
        video_clips = [VideoFileClip(path) for path in video_paths]
        
        # Убираем звук из всех видео
        video_clips = [clip.without_audio() for clip in video_clips]
        
        # Объединяем видео
        combined_video = concatenate_videoclips(video_clips, method="compose")
        
        # Загружаем аудио
        audio = AudioFileClip(audio_path)
        audio_duration = audio.duration
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
        
        # Добавляем аудио к видео
        final_video = combined_video.set_audio(audio)
        
        # Генерируем субтитры
        subtitles = self._generate_subtitles(text_for_subtitles, audio_duration)
        
        # Добавляем субтитры
        final_video = self._add_subtitles(final_video, subtitles)
        
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
        audio.close()
        final_video.close()
        
        return str(output_path), final_video.duration
    
    def _generate_subtitles(self, text: str, audio_duration: float) -> List[dict]:
        """
        Генерирует субтитры с умной синхронизацией
        """
        # Удаляем эмоциональные теги из текста
        clean_text = re.sub(r'\[.*?\]', '', text)
        
        # Разбиваем текст на предложения
        sentences = re.split(r'[.!?]+', clean_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Рассчитываем время для каждого предложения
        time_per_sentence = audio_duration / len(sentences)
        
        subtitles = []
        current_time = 0
        
        for sentence in sentences:
            # Разбиваем длинные предложения на части (для лучшей читаемости)
            words = sentence.split()
            if len(words) > 8:
                # Разбиваем на части по 6-8 слов
                chunks = [' '.join(words[i:i+7]) for i in range(0, len(words), 7)]
                chunk_duration = time_per_sentence / len(chunks)
                
                for chunk in chunks:
                    subtitles.append({
                        'text': chunk,
                        'start': current_time,
                        'end': current_time + chunk_duration
                    })
                    current_time += chunk_duration
            else:
                subtitles.append({
                    'text': sentence,
                    'start': current_time,
                    'end': current_time + time_per_sentence
                })
                current_time += time_per_sentence
        
        return subtitles
    
    def _add_subtitles(self, video: VideoFileClip, subtitles: List[dict]) -> CompositeVideoClip:
        """
        Добавляет субтитры к видео
        """
        subtitle_clips = []
        
        for sub in subtitles:
            # Создаём текстовый клип
            txt_clip = TextClip(
                sub['text'],
                fontsize=40,
                color='white',
                stroke_color='black',
                stroke_width=2,
                font='Arial-Bold',
                method='caption',
                size=(video.w * 0.9, None),
                align='center'
            )
            
            # Позиционируем субтитры внизу экрана
            txt_clip = txt_clip.set_position(('center', video.h * 0.75))
            txt_clip = txt_clip.set_start(sub['start'])
            txt_clip = txt_clip.set_duration(sub['end'] - sub['start'])
            
            subtitle_clips.append(txt_clip)
        
        # Объединяем видео с субтитрами
        final = CompositeVideoClip([video] + subtitle_clips)
        
        return final
    
    async def get_video_duration(self, video_path: str) -> float:
        """
        Получает длительность видео
        """
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.close()
        return duration

