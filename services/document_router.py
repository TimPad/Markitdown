from __future__ import annotations

import logging
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Callable


logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int], None]


@dataclass(frozen=True)
class ConversionResult:
    markdown: str
    method: str
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)


class DocumentRouter:
    OCR_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}

    def __init__(self, markitdown_service, ocr_service) -> None:
        self.markitdown_service = markitdown_service
        self.ocr_service = ocr_service

    @staticmethod
    def parse_page_range(page_range: str | None, total_pages: int) -> list[int]:
        if not page_range or not page_range.strip():
            return list(range(1, total_pages + 1))

        pages: list[int] = []
        for raw_part in page_range.split(","):
            part = raw_part.strip()
            if not part:
                continue

            if "-" in part:
                start_raw, end_raw = [item.strip() for item in part.split("-", 1)]
                start = int(start_raw)
                end = int(end_raw)
                if start > end:
                    raise ValueError("Диапазон страниц задан в обратном порядке.")
                pages.extend(range(start, end + 1))
            else:
                pages.append(int(part))

        unique_pages = sorted(set(pages))
        if not unique_pages:
            raise ValueError("Диапазон страниц пуст.")

        out_of_bounds = [page for page in unique_pages if page < 1 or page > total_pages]
        if out_of_bounds:
            raise ValueError(
                f"Страницы {out_of_bounds} за пределами документа из {total_pages} страниц."
            )

        return unique_pages

    def convert(
        self,
        file_bytes: bytes,
        filename: str,
        mode: str,
        language: str,
        dpi: int,
        max_pages: int,
        page_range: str | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> ConversionResult:
        extension = Path(filename).suffix.lower()

        if mode == "Без OCR":
            markdown = self.markitdown_service.convert(file_bytes, filename)
            return ConversionResult(markdown=markdown, method="markitdown")

        if mode == "Принудительный OCR" and extension not in self.OCR_EXTENSIONS:
            return ConversionResult(
                markdown="",
                method="unsupported",
                warnings=[f"OCR для формата {extension} не поддерживается."],
            )

        if extension == ".pdf":
            return self._convert_pdf(
                file_bytes=file_bytes,
                filename=filename,
                mode=mode,
                language=language,
                dpi=dpi,
                max_pages=max_pages,
                page_range=page_range,
                progress_callback=progress_callback,
            )

        if extension in self.OCR_EXTENSIONS:
            if mode in ("Автоматически", "Принудительный OCR"):
                return self._convert_images(
                    file_bytes=file_bytes,
                    language=language,
                    progress_callback=progress_callback,
                )

        markdown = self.markitdown_service.convert(file_bytes, filename)
        return ConversionResult(markdown=markdown, method="markitdown")

    def _convert_pdf(
        self,
        file_bytes: bytes,
        filename: str,
        mode: str,
        language: str,
        dpi: int,
        max_pages: int,
        page_range: str | None,
        progress_callback: ProgressCallback | None,
    ) -> ConversionResult:
        from services.pdf_service import extract_page_texts, find_scanned_pages

        page_texts = extract_page_texts(file_bytes)
        selected_pages = self.parse_page_range(page_range, len(page_texts))
        if len(selected_pages) > max_pages:
            raise ValueError(
                f"Выбрано {len(selected_pages)} страниц. Допустимый предел: {max_pages}."
            )

        if mode == "Принудительный OCR":
            return self._convert_pdf_pages_with_ocr(
                file_bytes, selected_pages, language, dpi, progress_callback
            )

        scanned_pages = set(find_scanned_pages(file_bytes))
        selected_scanned_pages = [page for page in selected_pages if page in scanned_pages]

        if not selected_scanned_pages:
            markdown = self.markitdown_service.convert(file_bytes, filename, pages=selected_pages)
            return ConversionResult(markdown=markdown, method="markitdown")

        if len(selected_scanned_pages) == len(selected_pages):
            return self._convert_pdf_pages_with_ocr(
                file_bytes, selected_pages, language, dpi, progress_callback
            )

        return self._convert_pdf_hybrid(
            file_bytes=file_bytes,
            filename=filename,
            selected_pages=selected_pages,
            scanned_pages=scanned_pages,
            language=language,
            dpi=dpi,
            progress_callback=progress_callback,
        )

    def _convert_images(
        self,
        file_bytes: bytes,
        language: str,
        progress_callback: ProgressCallback | None,
    ) -> ConversionResult:
        from PIL import Image, ImageSequence

        source = Image.open(BytesIO(file_bytes))
        frames = [frame.convert("RGB") for frame in ImageSequence.Iterator(source)]
        total = len(frames)
        warnings: list[str] = []
        parts: list[str] = []

        for page_number, image in enumerate(frames, start=1):
            try:
                markdown = self.ocr_service.recognize_page(image, page_number, language)
            except Exception as exc:
                markdown = ""
                warnings.append(f"Страница {page_number}: OCR не выполнен: {exc}")

            if total > 1:
                parts.append(f"<!-- page: {page_number} -->\n\n{markdown}")
            else:
                parts.append(markdown)

            if progress_callback:
                progress_callback(page_number, total)

        return ConversionResult(
            markdown="\n\n---\n\n".join(parts),
            method="nebius_ocr",
            warnings=warnings,
        )

    def _convert_pdf_pages_with_ocr(
        self,
        file_bytes: bytes,
        selected_pages: list[int],
        language: str,
        dpi: int,
        progress_callback: ProgressCallback | None,
    ) -> ConversionResult:
        from services.pdf_service import render_pdf_pages

        rendered_pages = render_pdf_pages(file_bytes, dpi=dpi, pages=selected_pages)
        total = len(rendered_pages)
        parts: list[str] = []
        warnings: list[str] = []

        for index, (page_number, image) in enumerate(rendered_pages, start=1):
            try:
                markdown = self.ocr_service.recognize_page(image, page_number, language)
            except Exception as exc:
                markdown = f"[OCR не выполнен для страницы {page_number}]"
                warnings.append(f"Страница {page_number}: OCR не выполнен: {exc}")

            parts.append(f"<!-- page: {page_number} -->\n\n{markdown}")
            if progress_callback:
                progress_callback(index, total)

        return ConversionResult(
            markdown="\n\n---\n\n".join(parts),
            method="nebius_ocr",
            warnings=warnings,
        )

    def _convert_pdf_hybrid(
        self,
        file_bytes: bytes,
        filename: str,
        selected_pages: list[int],
        scanned_pages: set[int],
        language: str,
        dpi: int,
        progress_callback: ProgressCallback | None,
    ) -> ConversionResult:
        from services.pdf_service import render_pdf_pages

        ocr_pages = [page for page in selected_pages if page in scanned_pages]
        digital_pages = [page for page in selected_pages if page not in scanned_pages]
        rendered_by_page = {
            page_number: image
            for page_number, image in render_pdf_pages(file_bytes, dpi=dpi, pages=ocr_pages)
        }
        warnings: list[str] = []
        parts: list[str] = []
        total = len(selected_pages)

        for index, page_number in enumerate(selected_pages, start=1):
            if page_number in scanned_pages:
                try:
                    markdown = self.ocr_service.recognize_page(
                        rendered_by_page[page_number], page_number, language
                    )
                except Exception as exc:
                    markdown = f"[OCR не выполнен для страницы {page_number}]"
                    warnings.append(f"Страница {page_number}: OCR не выполнен: {exc}")
            else:
                markdown = self.markitdown_service.convert(
                    file_bytes, filename, pages=[page_number]
                )

            parts.append(f"<!-- page: {page_number} -->\n\n{markdown}")
            if progress_callback:
                progress_callback(index, total)

        logger.info(
            "Hybrid PDF: %s OCR pages, %s digital pages", len(ocr_pages), len(digital_pages)
        )
        return ConversionResult(
            markdown="\n\n---\n\n".join(parts),
            method="hybrid",
            warnings=warnings,
            info=[
                f"Распознано OCR: страницы {ocr_pages}; "
                f"через MarkItDown: {digital_pages}"
            ],
        )
