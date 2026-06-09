from __future__ import annotations

import base64
from io import BytesIO

from tenacity import retry, stop_after_attempt, wait_exponential


SYSTEM_PROMPT = """Ты OCR-движок для конвертации документов в Markdown.
Возвращай только Markdown без обрамляющего блока кода и без комментариев от себя.
Сохраняй порядок чтения, заголовки, списки, таблицы, номера, даты, формулы и обозначения.
Не пересказывай и не сокращай текст. Неразборчивые фрагменты отмечай как [неразборчиво]."""


class NebiusOCRService:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: int = 120,
    ) -> None:
        from openai import OpenAI

        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    @staticmethod
    def image_to_data_url(image) -> str:
        buffer = BytesIO()
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        image.save(buffer, format="JPEG", quality=90, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded}"

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def recognize_page(self, image, page_number: int, language: str = "auto") -> str:
        image_url = self.image_to_data_url(image)
        user_message = (
            f"Распознай страницу {page_number}. Язык документа: {language}. "
            "Верни результат в Markdown."
        )

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_message},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ],
        )

        return (response.choices[0].message.content or "").strip()
