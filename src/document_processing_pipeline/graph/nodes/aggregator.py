from __future__ import annotations

from document_processing_pipeline.graph.state import ClaimGraphState


def aggregator_node(state: ClaimGraphState) -> dict:
    return {"final_output": {
        "claim_id": state["claim_id"],
        "id_data": state["id_data"].model_dump(),
        "discharge_summary_data": state["discharge_summary_data"].model_dump(),
        "itemized_bill_data": state["itemized_bill_data"].model_dump(),
        "page_classification": [item.model_dump() for item in state["page_classification"]],
        "errors": state["errors"],
        "metadata": state["metadata"],
    }}
