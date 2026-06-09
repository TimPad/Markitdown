from __future__ import annotations

from io import BytesIO


def extract_page_texts(pdf_bytes: bytes) -> list[str]:
    import fitz

    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        return [page.get_text("text").strip() for page in document]
    finally:
        document.close()


def extract_page_text_lengths(pdf_bytes: bytes) -> list[int]:
    return [len(text) for text in extract_page_texts(pdf_bytes)]


def find_scanned_pages(
    pdf_bytes: bytes,
    minimum_chars_per_page: int = 40,
) -> list[int]:
    lengths = extract_page_text_lengths(pdf_bytes)
    return [index + 1 for index, length in enumerate(lengths) if length < minimum_chars_per_page]


def render_pdf_pages(pdf_bytes: bytes, dpi: int = 180, pages: list[int] | None = None):
    import fitz
    from PIL import Image

    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    selected = set(pages or range(1, document.page_count + 1))
    scale = dpi / 72
    matrix = fitz.Matrix(scale, scale)
    images = []

    try:
        for page_index, page in enumerate(document, start=1):
            if page_index not in selected:
                continue

            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = Image.open(BytesIO(pixmap.tobytes("png"))).convert("RGB")
            images.append((page_index, image))
    finally:
        document.close()

    return images
