from __future__ import annotations

from document_processing_pipeline.graph.state import ClaimGraphState
from document_processing_pipeline.llm.gemini_client import GeminiClient
from document_processing_pipeline.schemas.contracts import PagePayload, SegregationResult

SEGREGATOR_LABELS = [
    "claim_forms",
    "cheque_or_bank_details",
    "identity_document",
    "itemized_bill",
    "discharge_summary",
    "prescription",
    "investigation_report",
    "cash_receipt",
    "other",
]


def segregator_node(state: ClaimGraphState) -> dict:
    client = GeminiClient()
    pages = state["pages"]
    page_images = state["page_images"]
    prompt = (
        "You are a medical claims document classifier. For each provided page, classify into exactly "
        f"one label from: {SEGREGATOR_LABELS}. Return JSON only in this shape: "
        '{"classifications":[{"page_number":1,"document_type":"identity_document"}]}. '
        "Do not skip any page."
    )
    page_text_hints = "\n".join(
        [f"Page {p.page_number} extracted_text: {p.text[:600]}" for p in pages if p.text]
    )
    if page_text_hints:
        prompt += f"\n\nText hints:\n{page_text_hints}"

    media_parts = [
        (page_images[p.page_number], "image/png")
        for p in pages
        if p.image_available and p.page_number in page_images
    ]
    payload = client.generate_json(prompt, media_parts=media_parts)
    raw_results = payload.get("classifications", [])
    if not isinstance(raw_results, list) or not raw_results:
        raise RuntimeError("upstream_model_unavailable")

    by_page_number = {p.page_number: p for p in pages}
    classifications: list[SegregationResult] = []
    errors: list[str] = []

    for raw_item in raw_results:
        try:
            item = SegregationResult.model_validate(raw_item)
        except Exception:
            errors.append("segregator_returned_invalid_item")
            continue
        if item.page_number not in by_page_number:
            errors.append("segregator_returned_unknown_page_number")
            continue
        classifications.append(item)

    # Guarantee one classification per input page so routing is deterministic.
    classified_page_numbers = {item.page_number for item in classifications}
    for page in pages:
        if page.page_number in classified_page_numbers:
            continue
        classifications.append(
            SegregationResult(page_number=page.page_number, document_type="other")
        )
        errors.append("segregator_missing_page_classification_defaulted_to_other")

    by_page = by_page_number
    id_pages: list[PagePayload] = []
    discharge_pages: list[PagePayload] = []
    bill_pages: list[PagePayload] = []

    for item in classifications:
        page = by_page.get(item.page_number)
        if page is None:
            continue
        if item.document_type == "identity_document":
            id_pages.append(page)
        elif item.document_type == "discharge_summary":
            discharge_pages.append(page)
        elif item.document_type == "itemized_bill":
            bill_pages.append(page)

    return {
        "page_classification": classifications,
        "id_pages": id_pages,
        "discharge_pages": discharge_pages,
        "itemized_bill_pages": bill_pages,
        "errors": state["errors"] + errors,
    }
