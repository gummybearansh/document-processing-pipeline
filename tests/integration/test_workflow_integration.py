from document_processing_pipeline.graph.workflow import build_claim_graph
from document_processing_pipeline.schemas.contracts import (
    DischargeSummaryData,
    IdentityData,
    ItemizedBillData,
    PagePayload,
)


def test_workflow_produces_final_output(monkeypatch):
    def fake_generate_json(self, prompt: str, media_parts=None):
        if "classifier" in prompt:
            return {
                "classifications": [
                    {"page_number": 1, "document_type": "identity_document"},
                    {"page_number": 2, "document_type": "discharge_summary"},
                    {"page_number": 3, "document_type": "itemized_bill"},
                ]
            }
        if "identity information" in prompt:
            return {
                "patient_name": "Alice",
                "date_of_birth": "1990-01-01",
                "id_numbers": ["ABC123"],
                "policy_details": "Policy-9",
            }
        if "discharge summary information" in prompt:
            return {
                "diagnosis": "Migraine",
                "admit_date": "2026-01-01",
                "discharge_date": "2026-01-02",
                "physician_details": "Dr. Smith",
            }
        return {
            "line_items": [
                {"description": "Room", "amount": 100.0},
                {"description": "Medicine", "amount": 50.0},
            ],
            "reported_total": 150.0,
        }

    monkeypatch.setattr(
        "document_processing_pipeline.llm.gemini_client.GeminiClient.generate_json",
        fake_generate_json,
    )

    graph = build_claim_graph()
    state = {
        "claim_id": "claim-123",
        "pages": [
            PagePayload(page_number=1, text="Patient Alice"),
            PagePayload(page_number=2, text="Discharge summary"),
            PagePayload(page_number=3, text="Bill items"),
        ],
        "page_images": {},
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
    output = graph.invoke(state)
    assert output["final_output"]["claim_id"] == "claim-123"
    assert output["final_output"]["id_data"]["patient_name"] == "Alice"
    assert output["final_output"]["itemized_bill_data"]["computed_total"] == 150.0
