from __future__ import annotations

from document_processing_pipeline.graph.state import ClaimGraphState
from document_processing_pipeline.llm.gemini_client import GeminiClient
from document_processing_pipeline.schemas.contracts import IdentityData


def id_agent_node(state: ClaimGraphState) -> dict:
    if not state["id_pages"]:
        return {"id_data": IdentityData()}

    client = GeminiClient()
    page_images = state["page_images"]
    media_parts = [
        (page_images[p.page_number], "image/png")
        for p in state["id_pages"]
        if p.image_available and p.page_number in page_images
    ]
    page_text = "\n\n".join([f"Page {p.page_number}:\n{p.text}" for p in state["id_pages"]])
    prompt = (
        "Extract identity information from the provided pages. Return JSON with keys: "
        "patient_name, date_of_birth, id_numbers, policy_details. "
        "Use null when unknown and do not hallucinate fields.\n\n"
        f"{page_text}"
    )
    payload = client.generate_json(prompt, media_parts=media_parts)
    if "id_numbers" in payload and isinstance(payload["id_numbers"], str):
        payload["id_numbers"] = [payload["id_numbers"]]
    return {"id_data": IdentityData.model_validate(payload)}
