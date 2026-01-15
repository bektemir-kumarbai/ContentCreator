import google.generativeai as genai
from config import settings
from typing import Dict, List
import json
import base64
from pathlib import Path


class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.text_model = genai.GenerativeModel(settings.gemini_text_model)
        self.image_model = genai.GenerativeModel(settings.gemini_image_model)
        self.chat_session = None
    
    async def rewrite_for_tts(self, original_text: str) -> str:
        """
        Переписывает текст притчи для озвучки с эмоциональными тегами
        """
        prompt = f"""
Ты — профессиональный сценарист для аудиоконтента.

Твоя задача: переписать текст притчи специально для озвучки голосовым синтезатором.

ТРЕБОВАНИЯ:
1. Сделай текст выразительным и драматургическим
2. Добавь эмоциональные теги для ElevenLabs:
   - [whispers] — шёпот
   - [sarcastically] — сарказм
   - [giggles] — смешок
   - [pause] — пауза
   - [dramatically] — драматично
   - [softly] — мягко
   - [excited] — взволнованно
3. Сохрани язык оригинального текста (не переводи!)
4. Текст должен быть коротким — для видео до 60 секунд
5. Используй короткие предложения для лучшей озвучки

ОРИГИНАЛЬНЫЙ ТЕКСТ:
{original_text}

ПЕРЕПИСАННЫЙ ТЕКСТ ДЛЯ ОЗВУЧКИ:
"""
        
        response = self.text_model.generate_content(prompt)
        return response.text.strip()
    
    async def generate_metadata_and_prompts(self, original_text: str, tts_text: str) -> Dict:
        """
        Генерирует метаданные для YouTube и промпты для изображений
        """
        prompt = f"""
Ты — эксперт по созданию контента для YouTube Shorts.

ОРИГИНАЛЬНАЯ ПРИТЧА:
{original_text}

ТЕКСТ ДЛЯ ОЗВУЧКИ:
{tts_text}

Твоя задача — создать:

1. ЗАГОЛОВОК для YouTube Shorts (до 100 символов, цепляющий)
2. ОПИСАНИЕ для YouTube (2-3 предложения)
3. ХЭШТЕГИ (5-10 релевантных хэштегов)
4. ПРОМПТЫ ДЛЯ ГЕНЕРАЦИИ ИЗОБРАЖЕНИЙ (3-7 промптов)

ВАЖНО про промпты для изображений:
- Каждый промпт = отдельная сцена истории
- Промпты должны быть последовательными и связанными
- Описывай стиль: "cinematic, dramatic lighting, detailed, 4K"
- Описывай персонажей детально (чтобы они были одинаковыми на всех изображениях)
- Промпты на английском языке
- Формат: короткое описание сцены + стиль

Верни результат СТРОГО в формате JSON:
{{
  "youtube_title": "заголовок",
  "youtube_description": "описание",
  "youtube_hashtags": "#хэштег1 #хэштег2 #хэштег3",
  "image_prompts": [
    "промпт для сцены 1",
    "промпт для сцены 2",
    "промпт для сцены 3"
  ]
}}
"""
        
        response = self.text_model.generate_content(prompt)
        text = response.text.strip()
        
        # Извлекаем JSON из ответа
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        return json.loads(text)
    
    async def generate_images_with_context(self, prompts: List[str], parable_id: int) -> List[str]:
        """
        Генерирует изображения в режиме чата для сохранения контекста
        """
        # Начинаем новую сессию чата
        self.chat_session = self.image_model.start_chat(history=[])
        
        generated_images = []
        
        # Первое изображение - задаём стиль и контекст
        first_prompt = f"""
Create the first scene of a visual story. This is scene 1 of {len(prompts)}.

IMPORTANT STYLE REQUIREMENTS:
- Cinematic, dramatic composition
- Consistent art style (choose one: realistic, anime, or illustrated)
- Rich colors and atmospheric lighting
- Vertical format (9:16 ratio for YouTube Shorts)
- High detail and quality

SCENE DESCRIPTION:
{prompts[0]}

Remember the characters, style, and atmosphere - they must remain consistent in all following scenes.
"""
        
        response = self.chat_session.send_message([first_prompt])
        
        # Сохраняем первое изображение
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data'):
                    image_path = self._save_image(part.inline_data.data, parable_id, 0)
                    generated_images.append(image_path)
                    break
        
        # Генерируем остальные изображения с контекстом
        for idx, prompt in enumerate(prompts[1:], start=1):
            continuation_prompt = f"""
Continue the visual story. This is scene {idx + 1} of {len(prompts)}.

CRITICAL: Maintain the SAME art style, characters, and atmosphere as previous scenes!

SCENE DESCRIPTION:
{prompt}

Keep all characters and visual style consistent with what you've already created.
"""
            
            response = self.chat_session.send_message([continuation_prompt])
            
            # Сохраняем изображение
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data'):
                        image_path = self._save_image(part.inline_data.data, parable_id, idx)
                        generated_images.append(image_path)
                        break
        
        return generated_images
    
    def _save_image(self, image_data: bytes, parable_id: int, scene_order: int) -> str:
        """
        Сохраняет изображение на диск
        """
        image_dir = settings.upload_dir / "images" / str(parable_id)
        image_dir.mkdir(parents=True, exist_ok=True)
        
        image_path = image_dir / f"scene_{scene_order}.png"
        
        # Если data в base64, декодируем
        if isinstance(image_data, str):
            image_data = base64.b64decode(image_data)
        
        with open(image_path, 'wb') as f:
            f.write(image_data)
        
        return str(image_path)

