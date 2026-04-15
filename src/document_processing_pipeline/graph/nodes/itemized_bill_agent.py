from __future__ import annotations

from document_processing_pipeline.graph.state import ClaimGraphState
from document_processing_pipeline.llm.gemini_client import GeminiClient
from document_processing_pipeline.schemas.contracts import ItemizedBillData


def itemized_bill_agent_node(state: ClaimGraphState) -> dict:
    if not state["itemized_bill_pages"]:
        return {"itemized_bill_data": ItemizedBillData()}

    client = GeminiClient()
    page_images = state["page_images"]
    media_parts = [
        (page_images[p.page_number], "image/png")
        for p in state["itemized_bill_pages"]
        if p.image_available and p.page_number in page_images
    ]
    page_text = "\n\n".join(
        [f"Page {p.page_number}:\n{p.text}" for p in state["itemized_bill_pages"]]
    )
    prompt = (
        "Extract itemized bill details from provided pages. Return JSON with keys: "
        "line_items (array of {description, amount}), reported_total. "
        "Extract all visible rows, and use null/empty when unavailable.\n\n"
        f"{page_text}"
    )
    payload = client.generate_json(prompt, media_parts=media_parts)
    line_items = payload.get("line_items")
    if isinstance(line_items, dict):
        payload["line_items"] = [line_items]
    if isinstance(payload.get("reported_total"), str):
        numeric = payload["reported_total"].replace(",", "").strip()
        try:
            payload["reported_total"] = float(numeric)
        except ValueError:
            payload["reported_total"] = None
    bill_data = ItemizedBillData.model_validate(payload)
    bill_data.computed_total = sum(item.amount for item in bill_data.line_items)
    return {"itemized_bill_data": bill_data}
