from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

from config import get_settings
from services.document_router import DocumentRouter
from services.markitdown_service import MarkItDownService
from services.nebius_ocr_service import NebiusOCRService
from services.validation_service import SUPPORTED_EXTENSIONS, validate_file


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


st.set_page_config(
    page_title="Документы в Markdown",
    page_icon="📄",
    layout="wide",
)


@st.cache_resource
def get_router() -> DocumentRouter:
    settings = get_settings(require_api_key=True)
    return DocumentRouter(
        markitdown_service=MarkItDownService(),
        ocr_service=NebiusOCRService(
            api_key=settings.nebius_api_key,
            base_url=settings.nebius_base_url,
            model=settings.nebius_ocr_model,
            timeout=settings.ocr_timeout_seconds,
            max_tokens=settings.ocr_max_tokens,
        ),
    )


settings = get_settings(require_api_key=False)

st.title("Преобразование документов в Markdown")
st.caption("Microsoft MarkItDown для цифровых документов и Nebius OCR для сканов")

if not settings.nebius_api_key:
    st.warning(
        "NEBIUS_API_KEY не задан. Режимы OCR будут недоступны до настройки Secrets."
    )

uploaded_file = st.file_uploader(
    "Документ",
    type=sorted(extension.removeprefix(".") for extension in SUPPORTED_EXTENSIONS),
)

mode = st.radio(
    "Режим обработки",
    ["Автоматически", "Без OCR", "Принудительный OCR"],
    horizontal=True,
)

left, right = st.columns(2)
with left:
    language = st.selectbox(
        "Язык OCR",
        ["auto", "Russian", "English", "Russian and English"],
    )
    page_range = st.text_input("Страницы", placeholder="например: 1-3, 7")

with right:
    dpi = st.slider(
        "DPI для PDF OCR",
        min_value=120,
        max_value=300,
        value=settings.ocr_render_dpi,
        step=20,
    )
    st.text_input("OCR-модель", value=settings.nebius_ocr_model, disabled=True)

if uploaded_file is not None:
    st.info(
        "При использовании OCR изображения страниц отправляются в Nebius Token Factory."
    )

    if st.button("Преобразовать", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status = st.empty()

        try:
            validate_file(
                filename=uploaded_file.name,
                file_size=uploaded_file.size,
                max_size_mb=settings.max_file_size_mb,
            )

            file_bytes = uploaded_file.getvalue()

            def update_progress(current: int, total: int) -> None:
                progress_bar.progress(current / total)
                status.info(f"Обработка страницы {current} из {total}")

            result = get_router().convert(
                file_bytes=file_bytes,
                filename=uploaded_file.name,
                mode=mode,
                language=language,
                dpi=dpi,
                max_pages=settings.ocr_max_pages,
                page_range=page_range,
                progress_callback=update_progress,
            )

            st.session_state["markdown"] = result.markdown
            st.session_state["method"] = result.method
            st.session_state["warnings"] = result.warnings
            st.session_state["info"] = result.info
            st.session_state["output_name"] = f"{Path(uploaded_file.name).stem}.md"

            progress_bar.progress(1.0)
            status.success(f"Готово. Метод: {result.method}")

        except Exception as exc:
            logger.exception("Не удалось обработать документ %s", uploaded_file.name)
            status.error(f"Не удалось обработать документ: {exc}")

if "markdown" in st.session_state:
    if st.session_state.get("info"):
        for note in st.session_state["info"]:
            st.info(note)

    if st.session_state.get("warnings"):
        for warning in st.session_state["warnings"]:
            st.warning(warning)

    preview_tab, source_tab = st.tabs(["Предпросмотр", "Исходный Markdown"])
    with preview_tab:
        st.markdown(st.session_state["markdown"])
    with source_tab:
        st.code(st.session_state["markdown"], language="markdown")

    st.download_button(
        "Скачать Markdown",
        data=st.session_state["markdown"].encode("utf-8"),
        file_name=st.session_state["output_name"],
        mime="text/markdown; charset=utf-8",
        use_container_width=True,
    )
