import unittest
from io import BytesIO

import fitz
from PIL import Image

from services.pdf_service import (
    extract_page_texts,
    find_scanned_pages,
    render_pdf_pages,
)


def _full_page_image_bytes() -> bytes:
    image = Image.new("RGB", (600, 800), color="gray")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _build_pdf() -> bytes:
    """3 страницы: цифровая, пустая (скан), большое изображение + короткая подпись."""
    document = fitz.open()

    digital = document.new_page()
    digital.insert_text((72, 72), "Digital page with a large amount of text content. " * 4)

    document.new_page()  # пустая → скан

    image_page = document.new_page()
    image_page.insert_image(image_page.rect, stream=_full_page_image_bytes())
    image_page.insert_text((72, 72), "Figure caption number one on this document page")

    data = document.tobytes()
    document.close()
    return data


class PdfServiceTest(unittest.TestCase):
    def setUp(self):
        self.pdf_bytes = _build_pdf()

    def test_extract_page_texts_returns_text_per_page(self):
        texts = extract_page_texts(self.pdf_bytes)
        self.assertEqual(len(texts), 3)
        self.assertIn("Digital page", texts[0])
        self.assertEqual(texts[1], "")

    def test_find_scanned_pages_flags_blank_and_image_pages(self):
        scanned = find_scanned_pages(self.pdf_bytes)
        # Страница 1 цифровая → не скан. Страница 2 пустая и страница 3 (картинка+подпись) → скан.
        self.assertEqual(scanned, [2, 3])

    def test_render_pdf_pages_returns_selected_images(self):
        rendered = render_pdf_pages(self.pdf_bytes, dpi=72, pages=[1, 3])
        page_numbers = [page_number for page_number, _ in rendered]
        self.assertEqual(page_numbers, [1, 3])
        self.assertTrue(all(isinstance(image, Image.Image) for _, image in rendered))


if __name__ == "__main__":
    unittest.main()
