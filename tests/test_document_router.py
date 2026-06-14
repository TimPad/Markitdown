import unittest
from io import BytesIO

import fitz
from PIL import Image

from services.document_router import DocumentRouter


class FakeMarkItDownService:
    def __init__(self):
        self.calls = []

    def convert(self, file_bytes: bytes, filename: str, pages=None) -> str:
        self.calls.append((file_bytes, filename, pages))
        suffix = "" if pages is None else f" pages={pages}"
        return f"markitdown:{filename}{suffix}"


class FakeOCRService:
    def __init__(self):
        self.calls = []

    def recognize_page(self, image, page_number: int, language: str = "auto") -> str:
        self.calls.append((page_number, language))
        if page_number == 2:
            raise RuntimeError("temporary OCR failure")
        return f"ocr-page-{page_number}-{language}"


class DocumentRouterTest(unittest.TestCase):
    def test_without_ocr_uses_markitdown(self):
        markitdown = FakeMarkItDownService()
        router = DocumentRouter(markitdown, FakeOCRService())

        result = router.convert(
            file_bytes=b"abc",
            filename="doc.docx",
            mode="Без OCR",
            language="Russian",
            dpi=180,
            max_pages=10,
        )

        self.assertEqual(result.markdown, "markitdown:doc.docx")
        self.assertEqual(result.method, "markitdown")
        self.assertEqual(markitdown.calls, [(b"abc", "doc.docx", None)])

    def test_forced_ocr_rejects_non_visual_formats(self):
        router = DocumentRouter(FakeMarkItDownService(), FakeOCRService())

        result = router.convert(
            file_bytes=b"abc",
            filename="doc.docx",
            mode="Принудительный OCR",
            language="auto",
            dpi=180,
            max_pages=10,
        )

        self.assertIn("OCR для формата .docx не поддерживается", result.warnings[0])
        self.assertEqual(result.markdown, "")

    def test_page_range_parser_supports_single_pages_and_ranges(self):
        self.assertEqual(
            DocumentRouter.parse_page_range("1, 3-5, 8", total_pages=10),
            [1, 3, 4, 5, 8],
        )

    def test_page_range_parser_rejects_out_of_bounds_pages(self):
        with self.assertRaisesRegex(ValueError, "за пределами"):
            DocumentRouter.parse_page_range("1-12", total_pages=10)


def _build_hybrid_pdf() -> bytes:
    """Страница 1 — пустая (скан), страницы 2 и 3 — цифровые."""
    document = fitz.open()
    document.new_page()
    for index in (2, 3):
        page = document.new_page()
        page.insert_text((72, 72), f"Digital page {index} with a sufficient amount of text. " * 3)
    data = document.tobytes()
    document.close()
    return data


def _build_multiframe_tiff() -> bytes:
    frames = [Image.new("RGB", (20, 20), color=color) for color in ("red", "green", "blue")]
    buffer = BytesIO()
    frames[0].save(buffer, format="TIFF", save_all=True, append_images=frames[1:])
    return buffer.getvalue()


class DocumentRouterHybridTest(unittest.TestCase):
    def test_hybrid_uses_markitdown_for_digital_pages(self):
        markitdown = FakeMarkItDownService()
        ocr = FakeOCRService()
        router = DocumentRouter(markitdown, ocr)

        result = router.convert(
            file_bytes=_build_hybrid_pdf(),
            filename="doc.pdf",
            mode="Автоматически",
            language="Russian",
            dpi=72,
            max_pages=10,
        )

        self.assertEqual(result.method, "hybrid")
        # OCR вызван только для сканированной страницы 1.
        self.assertEqual([page for page, _ in ocr.calls], [1])
        # Цифровые страницы 2 и 3 прошли через MarkItDown.
        self.assertEqual([call[2] for call in markitdown.calls], [[2], [3]])
        self.assertTrue(result.info)
        self.assertIn("[2, 3]", result.info[0])

    def test_multiframe_tiff_recognizes_all_frames(self):
        ocr = FakeOCRService()
        router = DocumentRouter(FakeMarkItDownService(), ocr)

        result = router.convert(
            file_bytes=_build_multiframe_tiff(),
            filename="scan.tiff",
            mode="Принудительный OCR",
            language="auto",
            dpi=72,
            max_pages=10,
        )

        self.assertEqual(result.method, "nebius_ocr")
        # Все три кадра отправлены в OCR.
        self.assertEqual([page for page, _ in ocr.calls], [1, 2, 3])
        # Кадр 2 у фейка падает → предупреждение.
        self.assertTrue(any("Страница 2" in warning for warning in result.warnings))


if __name__ == "__main__":
    unittest.main()
