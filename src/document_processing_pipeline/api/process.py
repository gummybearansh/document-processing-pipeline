from __future__ import annotations

from time import perf_counter

from document_processing_pipeline.graph.workflow import build_claim_graph
from document_processing_pipeline.schemas.contracts import (
    DischargeSummaryData,
    IdentityData,
    ItemizedBillData,
    ProcessResponse,
)
from document_processing_pipeline.services.pdf_text_extractor import (
    extract_pages_from_pdf,
    render_pdf_pages_to_png,
)
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

router = APIRouter(prefix="/api", tags=["process"])
claim_graph = build_claim_graph()


def build_initial_state(claim_id: str, pages, page_images):
    return {
        "claim_id": claim_id,
        "pages": pages,
        "page_images": page_images,
        "page_classification": [],
        "id_pages": [],
        "discharge_pages": [],
        "itemized_bill_pages": [],
        "id_data": IdentityData(),
        "discharge_summary_data": DischargeSummaryData(),
        "itemized_bill_data": ItemizedBillData(),
        "errors": [],
        "metadata": {},
        "final_output": {},
    }


@router.post("/process", response_model=ProcessResponse)
async def process_claim(claim_id: str = Form(...), file: UploadFile = File(...)) -> ProcessResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    contents = await file.read()
    pages = extract_pages_from_pdf(contents)
    page_images = render_pdf_pages_to_png(contents)
    for page in pages:
        page.image_available = page.page_number in page_images
    if not pages:
        raise HTTPException(status_code=400, detail="No pages found in PDF")

    start = perf_counter()
    try:
        final_state = claim_graph.invoke(
            build_initial_state(claim_id=claim_id, pages=pages, page_images=page_images)
        )
    except RuntimeError as exc:
        if str(exc) == "upstream_model_unavailable":
            raise HTTPException(status_code=503, detail="upstream_model_unavailable") from exc
        raise
    duration_ms = int((perf_counter() - start) * 1000)
    output = final_state["final_output"]
    output["metadata"]["processing_ms"] = duration_ms
    output["metadata"]["page_count"] = len(pages)
    return ProcessResponse.model_validate(output)
