from __future__ import annotations

import tempfile
from pathlib import Path


class MarkItDownService:
    def __init__(self) -> None:
        from markitdown import MarkItDown

        self.converter = MarkItDown()

    def convert(self, file_bytes: bytes, filename: str, pages=None) -> str:
        suffix = Path(filename).suffix
        temp_path: Path | None = None

        try:
            bytes_to_convert = file_bytes
            if pages and suffix.lower() == ".pdf":
                bytes_to_convert = self._pdf_subset(file_bytes, pages)

            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(bytes_to_convert)
                temp_path = Path(temp_file.name)

            result = self.converter.convert(str(temp_path))
            return (result.text_content or "").strip()
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    @staticmethod
    def _pdf_subset(file_bytes: bytes, pages: list[int]) -> bytes:
        import fitz

        source = fitz.open(stream=file_bytes, filetype="pdf")
        target = fitz.open()
        try:
            for page_number in pages:
                target.insert_pdf(source, from_page=page_number - 1, to_page=page_number - 1)
            return target.tobytes()
        finally:
            target.close()
            source.close()
