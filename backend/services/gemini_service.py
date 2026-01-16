import os
import mimetypes
from google import genai
from google.genai import types
from config import settings
from typing import Dict, List
import json
from pathlib import Path


class GeminiService:
    def __init__(self):
        # Получаем API ключ из настроек или переменных окружения
        api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY не найден! "
                "Создайте файл .env в корне проекта и добавьте: GEMINI_API_KEY=ваш_ключ\n"
                "Получить ключ можно здесь: https://aistudio.google.com/apikey"
            )
        
        # Используем новый клиент с API ключом
        self.client = genai.Client(api_key=api_key)
        self.text_model_name = settings.gemini_text_model
        self.image_model_name = settings.gemini_image_model
        self.chat_history = []
    
    async def rewrite_for_tts(self, original_text: str) -> str:
        """
        Переписывает текст притчи для озвучки с эмоциональными тегами
        """
        prompt = f"""
Ты — профессиональный сценарист для аудиоконтента.

Твоя задача: переписать текст притчи специально для озвучки голосовым синтезатором.

ТРЕБОВАНИЯ:
1. Сделай текст выразительным и драматургическим
2. Добавь эмоциональные теги для ElevenLabs (используй ТОЛЬКО эти теги):

   ЭМОЦИОНАЛЬНЫЕ СОСТОЯНИЯ:
   [excited] — возбуждение, волнение
   [nervous] — нервозность, беспокойство
   [frustrated] — разочарование, фрустрация
   [sorrowful] — печаль, скорбь
   [calm] — спокойствие, умиротворение

   РЕАКЦИИ:
   [sigh] — вздох
   [laughs] — смех
   [gulps] — глотание (от волнения)
   [gasps] — задыхание, удивление
   [whispers] — шепот

   КОГНИТИВНЫЕ ПАУЗЫ:
   [pauses] — пауза, раздумье
   [hesitates] — колебание, нерешительность
   [stammers] — заикание, запинка
   [resigned tone] — смиренный тон

   ТОНАЛЬНЫЕ ОТТЕНКИ:
   [cheerfully] — весело, радостно
   [flatly] — безэмоционально, монотонно
   [deadpan] — невозмутимо, с каменным лицом
   [playfully] — игриво, шутливо

3. НЕ используй другие теги (например [sad], [angry], [dramatically], [softly] и т.д.)
4. Сохрани язык оригинального текста (не переводи!)
5. Текст должен быть коротким — для видео до 60 секунд
6. Используй короткие предложения для лучшей озвучки
7. Верни ТОЛЬКО переписанный текст, без заголовков и пояснений

ОРИГИНАЛЬНЫЙ ТЕКСТ:
{original_text}
"""
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        
        response = self.client.models.generate_content(
            model=self.text_model_name,
            contents=contents,
        )
        
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

1. ЗАГОЛОВОК для YouTube Shorts (до 100 символов, цепляющий, НА РУССКОМ ЯЗЫКЕ)
2. ОПИСАНИЕ для YouTube (2-3 предложения, НА РУССКОМ ЯЗЫКЕ)
3. ХЭШТЕГИ (5-10 релевантных хэштегов, НА РУССКОМ ЯЗЫКЕ)
4. ПРОМПТЫ ДЛЯ ГЕНЕРАЦИИ ИЗОБРАЖЕНИЙ (3-7 промптов, НА АНГЛИЙСКОМ ЯЗЫКЕ)
5. ПРОМПТЫ ДЛЯ ГЕНЕРАЦИИ ВИДЕО (для каждого изображения, НА АНГЛИЙСКОМ ЯЗЫКЕ)

ВАЖНО:
- Заголовок, описание и хэштеги должны быть НА РУССКОМ ЯЗЫКЕ
- Промпты для изображений и видео должны быть НА АНГЛИЙСКОМ ЯЗЫКЕ

ВАЖНО про промпты для изображений:
- Каждый промпт = отдельная сцена истории
- Промпты должны быть последовательными и связанными
- Описывай стиль: "cinematic, dramatic lighting, detailed, 4K"
- Описывай персонажей детально (чтобы они были одинаковыми на всех изображениях)
- Формат: короткое описание сцены + стиль

ВАЖНО про промпты для видео:
- Каждый видео-промпт описывает ДВИЖЕНИЕ и ДЕЙСТВИЕ для соответствующей сцены
- Видео-промпт должен превратить статичное изображение в короткое видео (3-5 секунд)
- Описывай: движение камеры, анимацию объектов, эффекты
- Примеры: "Camera slowly zooms in, leaves gently sway in the wind", "Character turns head, dramatic lighting shifts"
- Формат: короткое описание движения и действия

Верни результат СТРОГО в формате JSON:
{{
  "youtube_title": "заголовок на русском",
  "youtube_description": "описание на русском",
  "youtube_hashtags": "#хэштег1 #хэштег2 #хэштег3",
  "image_prompts": [
    "prompt for scene 1 in English",
    "prompt for scene 2 in English",
    "prompt for scene 3 in English"
  ],
  "video_prompts": [
    "video animation prompt for scene 1 in English",
    "video animation prompt for scene 2 in English",
    "video animation prompt for scene 3 in English"
  ]
}}
"""
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        
        response = self.client.models.generate_content(
            model=self.text_model_name,
            contents=contents,
        )
        
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
        Использует официальный API gemini-2.5-flash-image
        Пропускает уже сгенерированные изображения
        """
        # Создаём директорию для изображений
        image_dir = settings.upload_dir / "images" / str(parable_id)
        image_dir.mkdir(parents=True, exist_ok=True)
        
        generated_images = []
        
        # Проверяем какие изображения уже существуют
        existing_images = {}
        for idx in range(len(prompts)):
            # Проверяем все возможные расширения (Gemini обычно генерирует JPEG)
            for ext in ['.jpeg', '.jpg', '.png', '.webp']:
                image_path = image_dir / f"scene_{idx}{ext}"
                if image_path.exists():
                    existing_images[idx] = str(image_path)
                    generated_images.append(str(image_path))
                    print(f"[Image Generation] ✅ Scene {idx + 1} already exists: {image_path}")
                    break
        
        # Если все изображения уже есть, возвращаем их
        if len(existing_images) == len(prompts):
            print(f"[Image Generation] ✅ All {len(prompts)} images already generated")
            return generated_images
        
        # Генерируем только недостающие изображения
        print(f"[Image Generation] Need to generate {len(prompts) - len(existing_images)} images")
        
        # ВАЖНО: Создаём общий контекст для всех сцен
        story_context = f"""You are creating a visual story with {len(prompts)} connected scenes.

CRITICAL REQUIREMENTS FOR CONSISTENCY:
1. SAME ART STYLE: Use identical artistic style, rendering technique, and visual quality across all scenes
2. SAME CHARACTERS: If characters appear, they must have the EXACT same face, body, clothing, and appearance
3. SAME COLOR PALETTE: Maintain consistent color grading, saturation, and mood
4. SAME LIGHTING: Keep similar lighting conditions and atmosphere
5. SAME LEVEL OF DETAIL: Maintain consistent quality and detail level
6. VERTICAL FORMAT: Always 9:16 ratio for YouTube Shorts

Think of this as frames from the same movie - everything must look like it belongs together."""
        
        for idx, prompt in enumerate(prompts):
            # Пропускаем уже существующие
            if idx in existing_images:
                continue
            
            print(f"[Image Generation] Generating scene {idx + 1}/{len(prompts)}...")
            print(f"[Image Generation] Prompt: {prompt[:100]}...")
            
            # Добавляем контекст предыдущих сцен
            scene_context = f"Scene {idx + 1} of {len(prompts)}"
            if idx > 0:
                scene_context += f"\n\nPREVIOUS SCENES CONTEXT:"
                scene_context += f"\n- You have already created {idx} scene(s) before this one"
                scene_context += f"\n- This scene MUST match the style and characters from previous scenes"
                scene_context += f"\n- Continue the visual narrative smoothly and consistently"
            
            full_prompt = f"""{story_context}

{scene_context}

SCENE DESCRIPTION:
{prompt}

STYLE: Cinematic, realistic, dramatic lighting, high quality, vertical 9:16 format."""
            
            # Создаём НОВЫЙ запрос для каждого изображения (без истории)
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=full_prompt)]
                )
            ]
            
            # Конфигурация для генерации изображений
            # ВАЖНО: убираем лишние запятые из JSON
            generate_content_config = types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                image_config=types.ImageConfig(
                    aspect_ratio="9:16"  # Вертикальный формат для YouTube Shorts
                )
            )
            
            image_saved = False
            text_parts = []
            
            try:
                for chunk in self.client.models.generate_content_stream(
                    model=self.image_model_name,
                    contents=contents,  # Передаём только текущий запрос
                    config=generate_content_config
                ):
                    if (
                        chunk.candidates is None
                        or not chunk.candidates
                        or chunk.candidates[0].content is None
                        or chunk.candidates[0].content.parts is None
                    ):
                        continue
                    
                    # Обрабатываем каждую часть ответа
                    for part in chunk.candidates[0].content.parts:
                        # СНАЧАЛА проверяем наличие изображения
                        if hasattr(part, 'inline_data') and part.inline_data:
                            if hasattr(part.inline_data, 'data') and part.inline_data.data and not image_saved:
                                inline_data = part.inline_data
                                data_buffer = inline_data.data
                                mime_type = inline_data.mime_type if hasattr(inline_data, 'mime_type') else 'image/jpeg'
                                
                                print(f"[Image Generation] 🎨 Found image data! mime_type: {mime_type}")
                                print(f"[Image Generation] Data type: {type(data_buffer)}")
                                print(f"[Image Generation] Data length: {len(data_buffer)}")
                                
                                # ВАЖНО: Декодируем base64
                                # Данные могут быть str или bytes, но в любом случае это base64
                                import base64
                                try:
                                    # Если это bytes, конвертируем в str для декодирования
                                    if isinstance(data_buffer, bytes):
                                        data_buffer = data_buffer.decode('utf-8')
                                        print(f"[Image Generation] Converted bytes to str")
                                    
                                    # Теперь декодируем base64
                                    print(f"[Image Generation] Decoding base64 data (length: {len(data_buffer)})...")
                                    data_buffer = base64.b64decode(data_buffer)
                                    print(f"[Image Generation] ✅ Decoded to {len(data_buffer)} bytes")
                                    
                                    # Проверяем что это действительно изображение
                                    if len(data_buffer) < 100:
                                        print(f"[Image Generation] ❌ Data too small, not an image!")
                                        continue
                                        
                                except Exception as e:
                                    print(f"[Image Generation] ❌ Base64 decode error: {e}")
                                    print(f"[Image Generation] First 100 chars: {str(data_buffer)[:100]}")
                                    continue
                                
                                # Определяем расширение из mime_type
                                file_extension = mimetypes.guess_extension(mime_type)
                                if not file_extension:
                                    # Fallback: если mime_type не распознан
                                    if 'jpeg' in mime_type.lower() or 'jpg' in mime_type.lower():
                                        file_extension = '.jpeg'
                                    elif 'png' in mime_type.lower():
                                        file_extension = '.png'
                                    elif 'webp' in mime_type.lower():
                                        file_extension = '.webp'
                                    else:
                                        file_extension = '.jpeg'  # По умолчанию JPEG
                                
                                print(f"[Image Generation] Extension: {file_extension}, Size: {len(data_buffer)} bytes")
                                
                                # Сохраняем изображение
                                file_name = f"scene_{idx}{file_extension}"
                                image_path = image_dir / file_name
                                
                                with open(image_path, "wb") as f:
                                    f.write(data_buffer)
                                
                                # Добавляем в нужную позицию
                                while len(generated_images) <= idx:
                                    generated_images.append(None)
                                generated_images[idx] = str(image_path)
                                
                                image_saved = True
                                print(f"[Image Generation] ✅ Scene {idx + 1} saved: {image_path}")
                        
                        # ПОТОМ собираем текстовые части (если есть)
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                
                # Если были текстовые части, выводим их
                if text_parts and not image_saved:
                    full_text = ''.join(text_parts)
                    print(f"[Image Generation] Model text response: {full_text[:200]}...")
                    print(f"[Image Generation] ⚠️  No image data received, only text!")
                
                if not image_saved:
                    print(f"[Image Generation] ⚠️  Warning: No image generated for scene {idx + 1}")
                    # Добавляем None чтобы сохранить порядок
                    while len(generated_images) <= idx:
                        generated_images.append(None)
                    generated_images[idx] = None
                    
            except Exception as e:
                print(f"[Image Generation] ❌ Error generating scene {idx + 1}: {str(e)}")
                # Добавляем None чтобы сохранить порядок
                while len(generated_images) <= idx:
                    generated_images.append(None)
                generated_images[idx] = None
                continue
        
        # Фильтруем None и возвращаем только успешные
        successful_images = [img for img in generated_images if img is not None]
        print(f"\n[Image Generation] ✅ Generated {len(successful_images)}/{len(prompts)} images")
        return successful_images
    
    # ═══════════════════════════════════════════════════════════════
    # ENGLISH TRANSLATION METHODS
    # ═══════════════════════════════════════════════════════════════
    
    async def translate_to_english_for_tts(self, russian_text: str) -> str:
        """
        Переводит русский текст на английский для озвучки
        """
        prompt = f"""
You are a professional translator and scriptwriter for audio content.

Your task: Translate Russian text to English specifically for voice-over by text-to-speech synthesizer.

REQUIREMENTS:
1. Make the text expressive and dramatic
2. Add emotional tags for ElevenLabs (use ONLY these tags):

   EMOTIONAL STATES:
   [excited] — excitement, agitation
   [nervous] — nervousness, anxiety
   [frustrated] — disappointment, frustration
   [sorrowful] — sadness, sorrow
   [calm] — calmness, peace

   REACTIONS:
   [sigh] — sigh
   [laughs] — laughter
   [gulps] — gulp (from excitement)
   [gasps] — gasp, surprise
   [whispers] — whisper

   COGNITIVE PAUSES:
   [pauses] — pause, reflection
   [hesitates] — hesitation, indecision
   [stammers] — stutter, stumble
   [resigned tone] — resigned tone

   TONAL NUANCES:
   [cheerfully] — cheerfully, joyfully
   [flatly] — emotionlessly, monotonously
   [deadpan] — impassively, deadpan
   [playfully] — playfully, jokingly

3. DO NOT use other tags (e.g. [sad], [angry], [dramatically], [softly], etc.)
4. Keep the text short — for videos up to 60 seconds
5. Use short sentences for better voice-over
6. Return ONLY the translated text, without headings or explanations

RUSSIAN TEXT:
{russian_text}
"""
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        
        response = self.client.models.generate_content(
            model=self.text_model_name,
            contents=contents,
        )
        
        return response.text.strip()
    
    async def generate_english_metadata_and_prompts(self, russian_tts_text: str, english_tts_text: str) -> Dict:
        """
        Генерирует английские метаданные для YouTube и промпты для изображений
        """
        prompt = f"""
You are an expert in creating content for YouTube Shorts.

RUSSIAN TTS TEXT (for context):
{russian_tts_text}

ENGLISH TTS TEXT:
{english_tts_text}

Your task — create:

1. TITLE for YouTube Shorts (up to 100 characters, catchy, IN ENGLISH)
2. DESCRIPTION for YouTube (2-3 sentences, IN ENGLISH)
3. HASHTAGS (5-10 relevant hashtags, IN ENGLISH)
4. IMAGE GENERATION PROMPTS (3-7 prompts, IN ENGLISH)
5. VIDEO GENERATION PROMPTS (for each image, IN ENGLISH)

IMPORTANT:
- Title, description, and hashtags must be IN ENGLISH
- Image and video prompts must be IN ENGLISH

IMPORTANT about image prompts:
- Each prompt = separate story scene
- Prompts should be sequential and connected
- Describe style: "cinematic, dramatic lighting, detailed, 4K"
- Describe characters in detail (so they are the same in all images)
- Format: short scene description + style

IMPORTANT about video prompts:
- Each video prompt describes MOVEMENT and ACTION for the corresponding scene
- Video prompt should turn a static image into a short video (3-5 seconds)
- Describe: camera movement, object animation, effects
- Examples: "Camera slowly zooms in, leaves gently sway in the wind", "Character turns head, dramatic lighting shifts"
- Format: short description of movement and action

Return result STRICTLY in JSON format:
{{
  "youtube_title": "title in English",
  "youtube_description": "description in English",
  "youtube_hashtags": "#hashtag1 #hashtag2 #hashtag3",
  "image_prompts": [
    "prompt for scene 1 in English",
    "prompt for scene 2 in English",
    "prompt for scene 3 in English"
  ],
  "video_prompts": [
    "video animation prompt for scene 1 in English",
    "video animation prompt for scene 2 in English",
    "video animation prompt for scene 3 in English"
  ]
}}
"""
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        
        response = self.client.models.generate_content(
            model=self.text_model_name,
            contents=contents,
        )
        
        text = response.text.strip()
        
        # Извлекаем JSON из ответа
        if "```json" in text:
            json_start = text.find("```json") + 7
            json_end = text.find("```", json_start)
            json_text = text[json_start:json_end].strip()
        elif "```" in text:
            json_start = text.find("```") + 3
            json_end = text.find("```", json_start)
            json_text = text[json_start:json_end].strip()
        else:
            json_text = text
        
        try:
            result = json.loads(json_text)
            return result
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Response text: {text}")
            raise ValueError(f"Failed to parse JSON response from Gemini: {e}")
    
    async def generate_hook(self, parable_text: str, language: str = "russian") -> str:
        """
        Генерирует цепляющий хук для первых 3 секунд видео
        
        Args:
            parable_text: Текст притчи
            language: Язык (russian или english)
        """
        if language == "russian":
            prompt = f"""
Ты — эксперт по созданию вирусного контента для YouTube Shorts.

Твоя задача: создать МАКСИМАЛЬНО ЦЕПЛЯЮЩЕЕ начало (хук) для притчи, которое заставит зрителя досмотреть до конца.

ПРИТЧА:
{parable_text[:300]}

ТРЕБОВАНИЯ К ХУКУ:
1. Длина: 1-2 коротких предложения (для озвучки за 3 секунды)
2. Должен создавать ИНТРИГУ или ШОК
3. Не раскрывать суть, а только заинтриговать
4. Использовать один из паттернов:
   - "Что если я скажу вам, что..."
   - "Этот человек потерял всё, но нашёл главное..."
   - "Никто не знал, что этот день изменит всё..."
   - "Однажды мудрец сказал слова, которые шокировали всех..."
   - "Эта история изменит ваш взгляд на..."
   - "То, что произошло дальше, никто не ожидал..."

5. ИЗБЕГАТЬ скучных начал типа "Однажды жил...", "В древние времена..."
6. Создавать эмоциональное напряжение
7. Обещать ценность или откровение

ВЕРНИ ТОЛЬКО ТЕКСТ ХУКА, БЕЗ ПОЯСНЕНИЙ.
"""
        else:  # english
            prompt = f"""
You are an expert in creating viral content for YouTube Shorts.

Your task: create a MAXIMALLY CATCHY hook for the first 3 seconds that will make viewers watch until the end.

PARABLE:
{parable_text[:300]}

HOOK REQUIREMENTS:
1. Length: 1-2 short sentences (for 3 seconds of voice-over)
2. Must create INTRIGUE or SHOCK
3. Don't reveal the essence, only intrigue
4. Use one of these patterns:
   - "What if I told you that..."
   - "This person lost everything, but found what matters most..."
   - "Nobody knew this day would change everything..."
   - "A wise man once said words that shocked everyone..."
   - "This story will change your perspective on..."
   - "What happened next, nobody expected..."

5. AVOID boring starts like "Once upon a time...", "In ancient times..."
6. Create emotional tension
7. Promise value or revelation

RETURN ONLY THE HOOK TEXT, NO EXPLANATIONS.
"""
        
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            ),
        ]
        
        response = self.client.models.generate_content(
            model=self.text_model_name,
            contents=contents,
        )
        
        hook = response.text.strip()
        
        # Убираем кавычки если LLM их добавил
        hook = hook.strip('"').strip("'").strip()
        
        return hook
    
    async def generate_hook_image_prompt(self, hook_text: str, parable_text: str, language: str = "russian") -> Dict[str, str]:
        """
        Генерирует промпты для изображения и видео хука
        
        Returns:
            Dict с ключами 'image_prompt' и 'video_prompt'
        """
        if language == "russian":
            prompt = f"""
Ты — эксперт по визуальному контенту для YouTube Shorts.

ХУК (первые 3 секунды):
{hook_text}

КОНТЕКСТ ПРИТЧИ:
{parable_text[:200]}

Твоя задача: создать МАКСИМАЛЬНО ЭФФЕКТНЫЙ визуальный промпт для первых 3 секунд видео.

ТРЕБОВАНИЯ:
1. Изображение должно быть ДРАМАТИЧНЫМ и ЦЕПЛЯЮЩИМ
2. Создавать интригу и желание смотреть дальше
3. Соответствовать хуку
4. Быть ярким, контрастным, привлекающим внимание
5. Можно использовать:
   - Крупный план лица с эмоцией
   - Драматичный момент действия
   - Загадочная атмосфера
   - Яркие цвета и контрасты

ВЕРНИ СТРОГО В ФОРМАТЕ JSON:
{{
  "image_prompt": "Детальный промпт для генерации изображения на английском",
  "video_prompt": "Промпт для генерации видео из этого изображения на английском"
}}

Промпты должны быть на АНГЛИЙСКОМ языке для Gemini/Grok!
"""
        else:  # english
            prompt = f"""
You are an expert in visual content for YouTube Shorts.

HOOK (first 3 seconds):
{hook_text}

PARABLE CONTEXT:
{parable_text[:200]}

Your task: create the MOST EFFECTIVE visual prompt for the first 3 seconds of video.

REQUIREMENTS:
1. Image must be DRAMATIC and CATCHY
2. Create intrigue and desire to watch further
3. Match the hook
4. Be bright, contrasting, attention-grabbing
5. Can use:
   - Close-up of face with emotion
   - Dramatic action moment
   - Mysterious atmosphere
   - Bright colors and contrasts

RETURN STRICTLY IN JSON FORMAT:
{{
  "image_prompt": "Detailed prompt for image generation in English",
  "video_prompt": "Prompt for video generation from this image in English"
}}

Prompts must be in ENGLISH for Gemini/Grok!
"""
        
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            ),
        ]
        
        response = self.client.models.generate_content(
            model=self.text_model_name,
            contents=contents,
        )
        
        text = response.text.strip()
        
        # Извлекаем JSON
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        try:
            result = json.loads(text)
            return {
                "image_prompt": result.get("image_prompt", ""),
                "video_prompt": result.get("video_prompt", "")
            }
        except json.JSONDecodeError as e:
            print(f"Error parsing hook prompts JSON: {e}")
            print(f"Response: {text}")
            # Возвращаем дефолтные промпты
            return {
                "image_prompt": f"Dramatic opening scene for: {hook_text}",
                "video_prompt": f"Cinematic video opening for: {hook_text}"
            }
    
    async def generate_title_variants(self, parable_text: str, language: str = "russian") -> List[Dict[str, str]]:
        """
        Генерирует 5 вариантов заголовков для A/B тестирования
        
        Returns:
            List of dicts with 'text' and 'type' keys
        """
        if language == "russian":
            prompt = f"""
Ты — эксперт по созданию вирусных заголовков для YouTube Shorts.

Твоя задача: создать 5 РАЗНЫХ вариантов заголовков для этой притчи.

ПРИТЧА:
{parable_text[:400]}

СОЗДАЙ 5 ВАРИАНТОВ ЗАГОЛОВКОВ:

1. ВОПРОС (question) - заголовок в форме вопроса, который заставляет задуматься
   Пример: "Что важнее: деньги или счастье?"

2. ИНТРИГА (intrigue) - создаёт загадку, обещает откровение
   Пример: "Мудрец раскрыл секрет, который изменит вашу жизнь"

3. ЭМОЦИЯ (emotion) - играет на эмоциях, создаёт сильное чувство
   Пример: "Эта история заставит вас плакать"

4. С ЦИФРАМИ (numbers) - использует конкретные числа
   Пример: "3 урока мудрости, которые изменят всё"

5. ПРОВОКАЦИЯ (provocation) - смелое утверждение, вызов
   Пример: "Вы всю жизнь делали это неправильно"

ТРЕБОВАНИЯ:
- Каждый заголовок до 100 символов
- Заголовки должны быть РАЗНЫМИ по стилю
- Цепляющие, вирусные, заставляющие кликнуть
- На русском языке

ВЕРНИ СТРОГО В ФОРМАТЕ JSON:
{{
  "variants": [
    {{"type": "question", "text": "заголовок 1"}},
    {{"type": "intrigue", "text": "заголовок 2"}},
    {{"type": "emotion", "text": "заголовок 3"}},
    {{"type": "numbers", "text": "заголовок 4"}},
    {{"type": "provocation", "text": "заголовок 5"}}
  ]
}}
"""
        else:  # english
            prompt = f"""
You are an expert in creating viral titles for YouTube Shorts.

Your task: create 5 DIFFERENT title variants for this parable.

PARABLE:
{parable_text[:400]}

CREATE 5 TITLE VARIANTS:

1. QUESTION - title in question form that makes you think
   Example: "What's more important: money or happiness?"

2. INTRIGUE - creates mystery, promises revelation
   Example: "A wise man revealed a secret that will change your life"

3. EMOTION - plays on emotions, creates strong feeling
   Example: "This story will make you cry"

4. NUMBERS - uses specific numbers
   Example: "3 lessons of wisdom that will change everything"

5. PROVOCATION - bold statement, challenge
   Example: "You've been doing this wrong your whole life"

REQUIREMENTS:
- Each title up to 100 characters
- Titles must be DIFFERENT in style
- Catchy, viral, making people click
- In English

RETURN STRICTLY IN JSON FORMAT:
{{
  "variants": [
    {{"type": "question", "text": "title 1"}},
    {{"type": "intrigue", "text": "title 2"}},
    {{"type": "emotion", "text": "title 3"}},
    {{"type": "numbers", "text": "title 4"}},
    {{"type": "provocation", "text": "title 5"}}
  ]
}}
"""
        
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            ),
        ]
        
        response = self.client.models.generate_content(
            model=self.text_model_name,
            contents=contents,
        )
        
        text = response.text.strip()
        
        # Извлекаем JSON
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        try:
            result = json.loads(text)
            return result.get("variants", [])
        except json.JSONDecodeError as e:
            print(f"Error parsing title variants JSON: {e}")
            print(f"Response: {text}")
            # Возвращаем пустой список если не удалось распарсить
            return []
    
    async def select_best_title(self, variants: List[Dict[str, str]], parable_text: str) -> int:
        """
        LLM выбирает лучший заголовок из вариантов
        
        Args:
            variants: Список вариантов с 'text' и 'type'
            parable_text: Текст притчи
        
        Returns:
            Индекс лучшего варианта (0-4)
        """
        variants_text = "\n".join([
            f"{i+1}. [{v['type']}] {v['text']}" 
            for i, v in enumerate(variants)
        ])
        
        prompt = f"""
Ты — эксперт по YouTube Shorts и вирусному контенту.

ПРИТЧА (краткое содержание):
{parable_text[:300]}

ВАРИАНТЫ ЗАГОЛОВКОВ:
{variants_text}

Твоя задача: выбрать ОДИН ЛУЧШИЙ заголовок, который:
1. Максимально привлечёт внимание
2. Заставит кликнуть на видео
3. Соответствует содержанию притчи
4. Имеет высокий потенциал виральности

Учитывай:
- Заголовки с вопросами часто работают хорошо
- Интрига создаёт желание узнать ответ
- Эмоции цепляют
- Цифры привлекают внимание
- Провокация вызывает реакцию

ВЕРНИ ТОЛЬКО НОМЕР (1-5) ЛУЧШЕГО ВАРИАНТА, БЕЗ ПОЯСНЕНИЙ.
"""
        
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            ),
        ]
        
        response = self.client.models.generate_content(
            model=self.text_model_name,
            contents=contents,
        )
        
        result = response.text.strip()
        
        # Извлекаем номер
        try:
            # Пытаемся найти цифру в ответе
            import re
            match = re.search(r'\d+', result)
            if match:
                number = int(match.group())
                # Конвертируем в индекс (1-5 -> 0-4)
                index = number - 1
                if 0 <= index < len(variants):
                    return index
        except:
            pass
        
        # Если не удалось распарсить, выбираем первый вариант
        print(f"[Gemini] Could not parse best title selection: {result}, defaulting to 0")
        return 0
    

