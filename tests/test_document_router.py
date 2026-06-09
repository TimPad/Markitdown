import unittest

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


if __name__ == "__main__":
    unittest.main()
