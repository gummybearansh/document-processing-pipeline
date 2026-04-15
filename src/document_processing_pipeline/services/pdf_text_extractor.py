from __future__ import annotations

from io import BytesIO

from document_processing_pipeline.schemas.contracts import PagePayload
import pymupdf
from pypdf import PdfReader


def extract_pages_from_pdf(file_bytes: bytes) -> list[PagePayload]:
    reader = PdfReader(BytesIO(file_bytes))
    pages: list[PagePayload] = []
    for idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(PagePayload(page_number=idx, text=text.strip()))
    return pages


def render_pdf_pages_to_png(file_bytes: bytes) -> dict[int, bytes]:
    doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    out: dict[int, bytes] = {}
    for idx in range(doc.page_count):
        page = doc.load_page(idx)
        pix = page.get_pixmap(dpi=150, alpha=False)
        out[idx + 1] = pix.tobytes("png")
    return out
