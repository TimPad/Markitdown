from __future__ import annotations

from io import BytesIO


def extract_page_texts(pdf_bytes: bytes) -> list[str]:
    import fitz

    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        return [page.get_text("text").strip() for page in document]
    finally:
        document.close()


def _page_image_coverage(page) -> float:
    """Доля площади страницы, занятая растровыми изображениями (0.0–1.0)."""
    page_area = abs(page.rect.width * page.rect.height)
    if page_area <= 0:
        return 0.0

    covered = 0.0
    for info in page.get_image_info():
        x0, y0, x1, y1 = info["bbox"]
        covered += abs((x1 - x0) * (y1 - y0))

    return min(covered / page_area, 1.0)


def find_scanned_pages(
    pdf_bytes: bytes,
    minimum_chars_per_page: int = 40,
    image_coverage_threshold: float = 0.5,
    max_chars_with_image: int = 200,
) -> list[int]:
    """Страницы, требующие OCR: почти без текста, либо большое изображение при скудном тексте."""
    import fitz

    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        scanned: list[int] = []
        for index, page in enumerate(document, start=1):
            text_length = len(page.get_text("text").strip())
            if text_length < minimum_chars_per_page:
                scanned.append(index)
                continue

            if (
                text_length < max_chars_with_image
                and _page_image_coverage(page) > image_coverage_threshold
            ):
                scanned.append(index)

        return scanned
    finally:
        document.close()


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
