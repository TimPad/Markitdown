import unittest

import fitz

from services.markitdown_service import MarkItDownService


def _build_three_page_pdf() -> bytes:
    document = fitz.open()
    for index in range(1, 4):
        page = document.new_page()
        page.insert_text((72, 72), f"Page number {index} with unique content")
    data = document.tobytes()
    document.close()
    return data


class MarkItDownServiceTest(unittest.TestCase):
    def test_pdf_subset_extracts_single_page(self):
        pdf_bytes = _build_three_page_pdf()

        subset = MarkItDownService._pdf_subset(pdf_bytes, [2])

        document = fitz.open(stream=subset, filetype="pdf")
        try:
            self.assertEqual(document.page_count, 1)
            text = document[0].get_text("text")
        finally:
            document.close()

        self.assertIn("Page number 2", text)
        self.assertNotIn("Page number 1", text)


if __name__ == "__main__":
    unittest.main()
