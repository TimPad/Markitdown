# MarkItDown Nebius OCR Service

Streamlit-приложение для конвертации документов в Markdown.

## Streamlit Cloud

1. Загрузите репозиторий в GitHub.
2. В Streamlit Cloud выберите `app.py` как entry point.
3. Добавьте Secrets:

```toml
NEBIUS_API_KEY = "your_api_key"
NEBIUS_BASE_URL = "https://api.tokenfactory.nebius.com/v1/"
NEBIUS_OCR_MODEL = "Qwen/Qwen2.5-VL-72B-Instruct"
MAX_FILE_SIZE_MB = "50"
OCR_MAX_PAGES = "100"
OCR_RENDER_DPI = "180"
OCR_TIMEOUT_SECONDS = "120"
```

## Локальный запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## Режимы

- `Автоматически`: цифровые PDF идут через MarkItDown, сканы через OCR, смешанные PDF обрабатываются постранично.
- `Без OCR`: файл целиком обрабатывается через MarkItDown.
- `Принудительный OCR`: PDF и изображения отправляются в Nebius OCR.
