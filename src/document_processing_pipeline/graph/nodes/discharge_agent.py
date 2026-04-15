from __future__ import annotations

from document_processing_pipeline.graph.state import ClaimGraphState
from document_processing_pipeline.llm.gemini_client import GeminiClient
from document_processing_pipeline.schemas.contracts import DischargeSummaryData


def discharge_summary_agent_node(state: ClaimGraphState) -> dict:
    if not state["discharge_pages"]:
        return {"discharge_summary_data": DischargeSummaryData()}

    client = GeminiClient()
    page_images = state["page_images"]
    media_parts = [
        (page_images[p.page_number], "image/png")
        for p in state["discharge_pages"]
        if p.image_available and p.page_number in page_images
    ]
    page_text = "\n\n".join([f"Page {p.page_number}:\n{p.text}" for p in state["discharge_pages"]])
    prompt = (
        "Extract discharge summary information from the provided pages. Return JSON with keys: "
        "diagnosis, admit_date, discharge_date, physician_details. "
        "Use null when unknown and do not hallucinate fields.\n\n"
        f"{page_text}"
    )
    payload = client.generate_json(prompt, media_parts=media_parts)
    return {"discharge_summary_data": DischargeSummaryData.model_validate(payload)}
