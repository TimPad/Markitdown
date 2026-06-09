# Инструкция по разработке сервиса конвертации документов в Markdown

## 1. Назначение сервиса

Сервис предназначен для преобразования документов в Markdown с использованием двух независимых механизмов:

1. **Microsoft MarkItDown** — для документов, содержащих цифровой текст и структурированные данные.
2. **OCR-модель через Nebius Token Factory** — для сканированных PDF, изображений и документов без текстового слоя.

Пользователь загружает файл, выбирает режим обработки и получает Markdown-файл.

Поддерживаемые режимы:

- **Без OCR** — документ обрабатывается только через MarkItDown.
- **Принудительный OCR** — документ преобразуется в изображения и отправляется в OCR-модель.
- **Автоматический режим** — сервис анализирует документ и самостоятельно определяет, требуется ли OCR.

---

## 2. Основной пользовательский сценарий

1. Пользователь открывает веб-приложение.
2. Загружает документ.
3. Выбирает режим обработки:
   - без OCR;
   - OCR;
   - автоматически.
4. При необходимости задаёт:
   - язык документа;
   - диапазон страниц;
   - разрешение рендеринга PDF;
   - OCR-модель.
5. Нажимает кнопку **«Преобразовать»**.
6. Сервис обрабатывает документ.
7. Пользователь получает:
   - предпросмотр Markdown;
   - исходный Markdown;
   - кнопку скачивания `.md`;
   - информацию о способе обработки;
   - предупреждения об ошибках отдельных страниц.

---

## 3. Рекомендуемая архитектура

```text
Пользователь
    |
    v
Streamlit-интерфейс
    |
    v
Валидатор файла
    |
    v
Маршрутизатор обработки
    |
    +----------------------------+
    |                            |
    v                            v
MarkItDown                 OCR-конвейер
    |                            |
    |                      PDF -> изображения
    |                            |
    |                      Nebius OCR API
    |                            |
    +-------------+--------------+
                  |
                  v
        Нормализация Markdown
                  |
                  v
       Предпросмотр и скачивание
```

Ключевой принцип: OCR не должен без необходимости запускаться для всех документов.

---

## 4. Логика выбора способа обработки

### 4.1. Режим «Без OCR»

Используется для:

- DOCX;
- PPTX;
- XLSX;
- HTML;
- CSV;
- JSON;
- XML;
- EPUB;
- обычных PDF с текстовым слоем.

Конвейер:

```text
Файл -> MarkItDown -> Markdown
```

### 4.2. Режим «Принудительный OCR»

Используется для:

- сканированных PDF;
- PNG;
- JPG;
- JPEG;
- TIFF;
- фотографий документов;
- PDF с повреждённым текстовым слоем;
- документов со сложной визуальной структурой.

Конвейер:

```text
Файл -> изображения страниц -> OCR-модель Nebius -> Markdown
```

### 4.3. Автоматический режим

Сервис извлекает текст из PDF и оценивает его объём.

Пример эвристики:

- менее 40 символов на странице — страница считается потенциальным сканом;
- если сканами являются более 70% страниц — документ направляется в OCR;
- если сканами являются только отдельные страницы — применяется гибридная обработка.

Конвейер:

```text
PDF
 |
 v
Анализ текстового слоя
 |
 +-- текста достаточно -> MarkItDown
 |
 +-- текста недостаточно -> OCR
```

---

## 5. Рекомендуемый технологический стек

### Основные компоненты

- Python 3.10 или новее;
- Streamlit;
- Microsoft MarkItDown;
- OpenAI Python SDK;
- Nebius Token Factory;
- PyMuPDF;
- Pillow;
- python-dotenv.

### Дополнительные компоненты

- Redis — кэш и хранение статусов;
- PostgreSQL — журнал заданий;
- Celery или RQ — фоновые задачи;
- Docker;
- Nginx;
- S3-совместимое хранилище;
- Sentry — мониторинг ошибок.

Для минимальной версии Redis, PostgreSQL и очередь задач не обязательны.

---

## 6. Структура проекта

```text
markitdown-ocr-service/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── Dockerfile
├── README.md
│
├── services/
│   ├── __init__.py
│   ├── document_router.py
│   ├── markitdown_service.py
│   ├── nebius_ocr_service.py
│   ├── pdf_service.py
│   ├── markdown_service.py
│   └── validation_service.py
│
├── models/
│   ├── __init__.py
│   └── schemas.py
│
├── utils/
│   ├── __init__.py
│   ├── hashing.py
│   ├── logging.py
│   └── retry.py
│
├── tests/
│   ├── test_router.py
│   ├── test_pdf_service.py
│   ├── test_validation.py
│   └── fixtures/
│
└── output/
```

---

## 7. Подготовка окружения

### 7.1. Создание виртуального окружения

```bash
python -m venv .venv
```

Linux и macOS:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\activate
```

### 7.2. Установка зависимостей

Создайте файл `requirements.txt`:

```txt
streamlit>=1.40
markitdown[all]
openai>=1.60
python-dotenv>=1.0
PyMuPDF>=1.24
Pillow>=10.0
tenacity>=8.2
pydantic>=2.0
```

Установите зависимости:

```bash
pip install -r requirements.txt
```

---

## 8. Конфигурация Nebius Token Factory

Создайте файл `.env`:

```env
NEBIUS_API_KEY=your_api_key
NEBIUS_BASE_URL=https://api.tokenfactory.nebius.com/v1
NEBIUS_OCR_MODEL=your_model_id

MAX_FILE_SIZE_MB=50
OCR_MAX_PAGES=100
OCR_RENDER_DPI=180
OCR_CONCURRENCY=3
OCR_TIMEOUT_SECONDS=120
```

Не помещайте `.env` в Git.

Добавьте в `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
output/
*.log
```

Для Streamlit Cloud используйте `.streamlit/secrets.toml`:

```toml
NEBIUS_API_KEY = "your_api_key"
NEBIUS_BASE_URL = "https://api.tokenfactory.nebius.com/v1"
NEBIUS_OCR_MODEL = "your_model_id"
```

---

## 9. Конфигурационный модуль

Файл `config.py`:

```python
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    nebius_api_key: str
    nebius_base_url: str
    nebius_ocr_model: str
    max_file_size_mb: int
    ocr_max_pages: int
    ocr_render_dpi: int
    ocr_concurrency: int
    ocr_timeout_seconds: int


def get_settings() -> Settings:
    api_key = os.getenv("NEBIUS_API_KEY", "").strip()
    model = os.getenv("NEBIUS_OCR_MODEL", "").strip()

    if not api_key:
        raise RuntimeError("Не задан NEBIUS_API_KEY")

    if not model:
        raise RuntimeError("Не задан NEBIUS_OCR_MODEL")

    return Settings(
        nebius_api_key=api_key,
        nebius_base_url=os.getenv(
            "NEBIUS_BASE_URL",
            "https://api.tokenfactory.nebius.com/v1",
        ),
        nebius_ocr_model=model,
        max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "50")),
        ocr_max_pages=int(os.getenv("OCR_MAX_PAGES", "100")),
        ocr_render_dpi=int(os.getenv("OCR_RENDER_DPI", "180")),
        ocr_concurrency=int(os.getenv("OCR_CONCURRENCY", "3")),
        ocr_timeout_seconds=int(
            os.getenv("OCR_TIMEOUT_SECONDS", "120")
        ),
    )
```

---

## 10. Сервис MarkItDown

Файл `services/markitdown_service.py`:

```python
from __future__ import annotations

import tempfile
from pathlib import Path

from markitdown import MarkItDown


class MarkItDownService:
    def __init__(self) -> None:
        self.converter = MarkItDown()

    def convert(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> str:
        suffix = Path(filename).suffix
        temp_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
            ) as temp_file:
                temp_file.write(file_bytes)
                temp_path = Path(temp_file.name)

            result = self.converter.convert(str(temp_path))
            return result.text_content.strip()

        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
```

---

## 11. Работа с PDF

Файл `services/pdf_service.py`:

```python
from __future__ import annotations

from io import BytesIO

import fitz
from PIL import Image


def render_pdf_pages(
    pdf_bytes: bytes,
    dpi: int = 180,
) -> list[Image.Image]:
    document = fitz.open(
        stream=pdf_bytes,
        filetype="pdf",
    )

    scale = dpi / 72
    matrix = fitz.Matrix(scale, scale)
    images: list[Image.Image] = []

    try:
        for page in document:
            pixmap = page.get_pixmap(
                matrix=matrix,
                alpha=False,
            )

            image = Image.open(
                BytesIO(pixmap.tobytes("png"))
            ).convert("RGB")

            images.append(image)

    finally:
        document.close()

    return images


def extract_page_text_lengths(
    pdf_bytes: bytes,
) -> list[int]:
    document = fitz.open(
        stream=pdf_bytes,
        filetype="pdf",
    )

    try:
        return [
            len(page.get_text("text").strip())
            for page in document
        ]
    finally:
        document.close()


def is_probably_scanned_pdf(
    pdf_bytes: bytes,
    minimum_chars_per_page: int = 40,
    scanned_page_ratio: float = 0.7,
) -> bool:
    lengths = extract_page_text_lengths(pdf_bytes)

    if not lengths:
        return True

    scanned_pages = sum(
        length < minimum_chars_per_page
        for length in lengths
    )

    return scanned_pages / len(lengths) >= scanned_page_ratio
```

---

## 12. OCR-сервис Nebius

Файл `services/nebius_ocr_service.py`:

```python
from __future__ import annotations

import base64
from io import BytesIO

from openai import OpenAI
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential


class NebiusOCRService:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: int = 120,
    ) -> None:
        self.model = model

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )

    @staticmethod
    def image_to_data_url(
        image: Image.Image,
    ) -> str:
        buffer = BytesIO()

        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        image.save(
            buffer,
            format="JPEG",
            quality=90,
            optimize=True,
        )

        encoded = base64.b64encode(
            buffer.getvalue()
        ).decode("utf-8")

        return f"data:image/jpeg;base64,{encoded}"

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(
            multiplier=1,
            min=1,
            max=8,
        ),
        reraise=True,
    )
    def recognize_page(
        self,
        image: Image.Image,
        page_number: int,
        language: str = "auto",
    ) -> str:
        image_url = self.image_to_data_url(image)

        prompt = f"""
Распознай страницу документа и верни только Markdown.

Требования:
1. Сохраняй порядок чтения.
2. Сохраняй заголовки и уровни заголовков.
3. Сохраняй нумерованные и маркированные списки.
4. Таблицы возвращай в формате Markdown.
5. Не пересказывай и не сокращай текст.
6. Не добавляй комментарии от себя.
7. Не помещай результат в общий блок кода.
8. Сохраняй номера, даты, формулы и обозначения.
9. Неразборчивые фрагменты отмечай как [неразборчиво].
10. Язык документа: {language}.
11. Номер страницы: {page_number}.
""".strip()

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                            },
                        },
                    ],
                }
            ],
        )

        return (
            response.choices[0].message.content or ""
        ).strip()
```

Точный идентификатор модели и поддерживаемый формат запроса следует сверять с документацией и интерфейсом Nebius Token Factory.

---

## 13. Валидация файлов

Файл `services/validation_service.py`:

```python
from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".pptx", ".xlsx", ".xls",
    ".html", ".htm", ".csv", ".json", ".xml",
    ".txt", ".md", ".epub", ".png", ".jpg",
    ".jpeg", ".webp", ".tif", ".tiff",
}


def validate_file(
    filename: str,
    file_size: int,
    max_size_mb: int,
) -> None:
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Формат {extension} не поддерживается."
        )

    max_size_bytes = max_size_mb * 1024 * 1024

    if file_size > max_size_bytes:
        raise ValueError(
            f"Размер файла превышает {max_size_mb} МБ."
        )

    if file_size == 0:
        raise ValueError("Загружен пустой файл.")
```

Для публичного сервиса дополнительно проверяйте MIME-тип и сигнатуру файла.

---

## 14. Маршрутизатор обработки

Файл `services/document_router.py`:

```python
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Callable

from PIL import Image

from services.markitdown_service import MarkItDownService
from services.nebius_ocr_service import NebiusOCRService
from services.pdf_service import (
    is_probably_scanned_pdf,
    render_pdf_pages,
)


ProgressCallback = Callable[[int, int], None]


class DocumentRouter:
    OCR_EXTENSIONS = {
        ".pdf", ".png", ".jpg", ".jpeg",
        ".webp", ".tif", ".tiff",
    }

    def __init__(
        self,
        markitdown_service: MarkItDownService,
        ocr_service: NebiusOCRService,
    ) -> None:
        self.markitdown_service = markitdown_service
        self.ocr_service = ocr_service

    def convert(
        self,
        file_bytes: bytes,
        filename: str,
        mode: str,
        language: str,
        dpi: int,
        max_pages: int,
        progress_callback: ProgressCallback | None = None,
    ) -> tuple[str, str]:
        extension = Path(filename).suffix.lower()

        if mode == "Без OCR":
            markdown = self.markitdown_service.convert(
                file_bytes=file_bytes,
                filename=filename,
            )
            return markdown, "markitdown"

        if mode == "Автоматически":
            if extension == ".pdf":
                use_ocr = is_probably_scanned_pdf(file_bytes)
            elif extension in self.OCR_EXTENSIONS:
                use_ocr = True
            else:
                use_ocr = False
        else:
            use_ocr = True

        if not use_ocr:
            markdown = self.markitdown_service.convert(
                file_bytes=file_bytes,
                filename=filename,
            )
            return markdown, "markitdown"

        if extension not in self.OCR_EXTENSIONS:
            raise ValueError(
                f"OCR для формата {extension} не поддерживается."
            )

        markdown = self._convert_with_ocr(
            file_bytes=file_bytes,
            extension=extension,
            language=language,
            dpi=dpi,
            max_pages=max_pages,
            progress_callback=progress_callback,
        )

        return markdown, "nebius_ocr"

    def _convert_with_ocr(
        self,
        file_bytes: bytes,
        extension: str,
        language: str,
        dpi: int,
        max_pages: int,
        progress_callback: ProgressCallback | None,
    ) -> str:
        if extension == ".pdf":
            images = render_pdf_pages(
                pdf_bytes=file_bytes,
                dpi=dpi,
            )
        else:
            images = [
                Image.open(BytesIO(file_bytes)).convert("RGB")
            ]

        if len(images) > max_pages:
            raise ValueError(
                f"В документе {len(images)} страниц. "
                f"Допустимый предел: {max_pages}."
            )

        parts: list[str] = []
        total = len(images)

        for page_number, image in enumerate(images, start=1):
            markdown = self.ocr_service.recognize_page(
                image=image,
                page_number=page_number,
                language=language,
            )

            parts.append(
                f"<!-- page: {page_number} -->\n\n"
                f"{markdown}"
            )

            if progress_callback:
                progress_callback(page_number, total)

        return "\n\n---\n\n".join(parts)
```

---

## 15. Streamlit-интерфейс

Файл `app.py`:

```python
from pathlib import Path

import streamlit as st

from config import get_settings
from services.document_router import DocumentRouter
from services.markitdown_service import MarkItDownService
from services.nebius_ocr_service import NebiusOCRService
from services.validation_service import validate_file


st.set_page_config(
    page_title="Документ в Markdown",
    page_icon="📄",
    layout="wide",
)


@st.cache_resource
def get_router() -> DocumentRouter:
    settings = get_settings()

    return DocumentRouter(
        markitdown_service=MarkItDownService(),
        ocr_service=NebiusOCRService(
            api_key=settings.nebius_api_key,
            base_url=settings.nebius_base_url,
            model=settings.nebius_ocr_model,
            timeout=settings.ocr_timeout_seconds,
        ),
    )


settings = get_settings()

st.title("Преобразование документов в Markdown")
st.caption("Microsoft MarkItDown и OCR через Nebius Token Factory")

uploaded_file = st.file_uploader(
    "Загрузите документ",
    type=[
        "pdf", "docx", "pptx", "xlsx", "xls",
        "html", "htm", "csv", "json", "xml",
        "txt", "md", "epub", "png", "jpg",
        "jpeg", "webp", "tif", "tiff",
    ],
)

mode = st.radio(
    "Режим обработки",
    options=[
        "Без OCR",
        "Принудительный OCR",
        "Автоматически",
    ],
    horizontal=True,
)

with st.expander("Настройки OCR"):
    language = st.selectbox(
        "Язык документа",
        options=[
            "auto",
            "Russian",
            "English",
            "Russian and English",
        ],
    )

    dpi = st.slider(
        "Разрешение рендеринга PDF",
        min_value=120,
        max_value=300,
        value=settings.ocr_render_dpi,
        step=20,
    )

if uploaded_file is not None:
    if st.button(
        "Преобразовать",
        type="primary",
        use_container_width=True,
    ):
        progress_bar = st.progress(0)
        status = st.empty()

        try:
            validate_file(
                filename=uploaded_file.name,
                file_size=uploaded_file.size,
                max_size_mb=settings.max_file_size_mb,
            )

            file_bytes = uploaded_file.getvalue()

            def update_progress(
                current: int,
                total: int,
            ) -> None:
                progress_bar.progress(current / total)
                status.info(
                    f"Обработка страницы {current} из {total}"
                )

            markdown, method = get_router().convert(
                file_bytes=file_bytes,
                filename=uploaded_file.name,
                mode=mode,
                language=language,
                dpi=dpi,
                max_pages=settings.ocr_max_pages,
                progress_callback=update_progress,
            )

            st.session_state["markdown"] = markdown
            st.session_state["method"] = method
            st.session_state["output_name"] = (
                f"{Path(uploaded_file.name).stem}.md"
            )

            progress_bar.progress(1.0)
            status.success(
                f"Обработка завершена. Метод: {method}"
            )

        except Exception as exc:
            status.error("Не удалось обработать документ.")
            st.exception(exc)

if "markdown" in st.session_state:
    markdown = st.session_state["markdown"]

    preview_tab, source_tab = st.tabs(
        ["Предпросмотр", "Исходный Markdown"]
    )

    with preview_tab:
        st.markdown(markdown)

    with source_tab:
        st.code(markdown, language="markdown")

    st.download_button(
        label="Скачать Markdown",
        data=markdown.encode("utf-8"),
        file_name=st.session_state["output_name"],
        mime="text/markdown; charset=utf-8",
        use_container_width=True,
    )
```

---

## 16. Запуск приложения

```bash
streamlit run app.py
```

По умолчанию приложение будет доступно по адресу:

```text
http://localhost:8501
```

---

## 17. Гибридная постраничная обработка

Для производственной версии рекомендуется анализировать каждую страницу PDF отдельно.

Алгоритм:

1. открыть PDF;
2. извлечь текст каждой страницы;
3. определить страницы с недостаточным количеством текста;
4. обычные страницы обработать локально;
5. сканированные страницы отправить в OCR;
6. собрать результат в исходном порядке.

Пример результата:

```markdown
<!-- page: 1 -->

Текст первой страницы, извлечённый локально.

---

<!-- page: 2 -->

Текст второй страницы, распознанный OCR.
```

Это снижает стоимость OCR и ускоряет обработку смешанных документов.

---

## 18. Обработка ошибок

Сервис должен различать:

- неподдерживаемый формат;
- слишком большой файл;
- слишком много страниц;
- повреждённый PDF;
- ошибку MarkItDown;
- ошибку OCR-модели;
- тайм-аут;
- превышение лимита API;
- пустой результат;
- ошибку отдельной страницы.

Не следует прерывать весь документ из-за одной неудачной страницы.

---

## 19. Кэширование

Для предотвращения повторной оплаты одинаковых OCR-запросов рассчитывайте SHA-256 файла:

```python
import hashlib


def calculate_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
```

Ключ кэша должен включать:

```text
SHA256 файла
+ модель
+ DPI
+ язык
+ версия OCR-промпта
+ диапазон страниц
```

---

## 20. Безопасность

Обязательные меры:

- хранить API-ключ только на сервере;
- не передавать ключ в браузер;
- ограничить размер файлов;
- ограничить количество страниц;
- удалять временные файлы;
- проверять расширение и MIME-тип;
- блокировать исполняемые файлы;
- не выполнять макросы;
- не хранить документы без необходимости;
- очищать журналы от содержимого документов.

Для публичного сервиса дополнительно рекомендуются:

- авторизация;
- лимит запросов;
- CAPTCHA;
- антивирусная проверка;
- изоляция обработки в контейнере;
- ограничение CPU и памяти;
- политика удаления документов.

---

## 21. Конфиденциальность

Перед отправкой документа во внешний OCR API пользователь должен понимать, что страницы передаются внешнему провайдеру.

Добавьте предупреждение:

```text
При включении OCR изображения страниц будут отправлены
в Nebius Token Factory для распознавания.
```

Для конфиденциальных документов можно добавить локальный OCR как резервный режим.

---

## 22. Тестирование

Проверить следующие типы документов:

1. цифровой PDF;
2. сканированный PDF;
3. смешанный PDF;
4. PDF с таблицами;
5. DOCX;
6. PPTX;
7. XLSX;
8. PNG;
9. повреждённый PDF;
10. документ на русском и английском.

Критерии качества OCR:

- полнота текста;
- порядок чтения;
- корректность таблиц;
- сохранение заголовков;
- корректность номеров и дат;
- отсутствие галлюцинаций;
- качество распознавания кириллицы.

---

## 23. Docker

Файл `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD [
  "streamlit",
  "run",
  "app.py",
  "--server.address=0.0.0.0",
  "--server.port=8501"
]
```

Сборка:

```bash
docker build -t markitdown-ocr-service .
```

Запуск:

```bash
docker run   --env-file .env   -p 8501:8501   markitdown-ocr-service
```

---

## 24. План разработки

### Этап 1. Минимальный прототип

- загрузка одного файла;
- режим без OCR;
- режим принудительного OCR;
- PDF и изображения;
- предпросмотр;
- скачивание `.md`;
- хранение ключа в `.env`.

### Этап 2. Автоматическое определение OCR

- анализ текстового слоя PDF;
- автоматический выбор режима;
- обработка смешанных документов;
- отображение причины выбора.

### Этап 3. Надёжность

- повторные попытки;
- тайм-ауты;
- постраничное восстановление;
- журнал ошибок;
- кэширование;
- ограничения размера и страниц.

### Этап 4. Производственная версия

- очередь задач;
- авторизация;
- база данных;
- S3-хранилище;
- мониторинг;
- разграничение доступа;
- контейнеризация;
- CI/CD.

---

## 25. Критерии готовности минимальной версии

Минимальная версия считается готовой, если:

- загружается PDF, DOCX и изображение;
- обычный PDF преобразуется через MarkItDown;
- сканированный PDF преобразуется через Nebius OCR;
- пользователь может выбрать режим;
- результат скачивается как `.md`;
- границы страниц сохраняются;
- ошибки отображаются в интерфейсе;
- API-ключ не попадает в клиентский код;
- временные файлы удаляются;
- размер и число страниц ограничены.

---

## 26. Итоговая схема

```text
DOCX / PPTX / XLSX / HTML
        |
        v
    MarkItDown
        |
        v
     Markdown


Цифровой PDF
        |
        v
    MarkItDown
        |
        v
     Markdown


Сканированный PDF / изображение
        |
        v
  Рендеринг страниц
        |
        v
   Nebius OCR API
        |
        v
     Markdown
```

Для первой версии рекомендуется использовать Streamlit как интерфейс, MarkItDown как основной конвертер, Nebius Token Factory как опциональный OCR-механизм и постраничную обработку PDF как базовую архитектурную единицу.
