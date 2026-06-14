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
    ocr_timeout_seconds: int
    ocr_max_tokens: int


def _secret_or_env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value

    try:
        import streamlit as st

        secret = st.secrets.get(name)
    except Exception:
        secret = None

    if secret is None:
        return default

    return str(secret)


def _int_setting(name: str, default: int) -> int:
    raw = _secret_or_env(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} должен быть целым числом") from exc

    if value <= 0:
        raise RuntimeError(f"{name} должен быть больше 0")

    return value


def get_settings(require_api_key: bool = True) -> Settings:
    api_key = _secret_or_env("NEBIUS_API_KEY").strip()
    if require_api_key and not api_key:
        raise RuntimeError(
            "Не задан NEBIUS_API_KEY. Для Streamlit Cloud добавьте его в Secrets."
        )

    return Settings(
        nebius_api_key=api_key,
        nebius_base_url=_secret_or_env(
            "NEBIUS_BASE_URL",
            "https://api.tokenfactory.nebius.com/v1/",
        ).strip(),
        nebius_ocr_model=_secret_or_env(
            "NEBIUS_OCR_MODEL",
            "Qwen/Qwen2.5-VL-72B-Instruct",
        ).strip(),
        max_file_size_mb=_int_setting("MAX_FILE_SIZE_MB", 50),
        ocr_max_pages=_int_setting("OCR_MAX_PAGES", 100),
        ocr_render_dpi=_int_setting("OCR_RENDER_DPI", 180),
        ocr_timeout_seconds=_int_setting("OCR_TIMEOUT_SECONDS", 120),
        ocr_max_tokens=_int_setting("OCR_MAX_TOKENS", 8192),
    )
