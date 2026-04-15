from fastapi.testclient import TestClient

from document_processing_pipeline.main import app
from document_processing_pipeline.schemas.contracts import PagePayload


def test_process_endpoint_returns_extracted_json(monkeypatch):
    def fake_extract_pages(_bytes: bytes):
        return [
            PagePayload(page_number=1, text="ID"),
            PagePayload(page_number=2, text="Discharge"),
            PagePayload(page_number=3, text="Bill"),
        ]

    def fake_render_pages(_bytes: bytes):
        return {}

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
            return {"patient_name": "Jane", "id_numbers": ["ID1"]}
        if "discharge summary information" in prompt:
            return {"diagnosis": "Viral fever"}
        return {"line_items": [{"description": "Test", "amount": 99.0}], "reported_total": 99.0}

    monkeypatch.setattr(
        "document_processing_pipeline.api.process.extract_pages_from_pdf",
        fake_extract_pages,
    )
    monkeypatch.setattr(
        "document_processing_pipeline.api.process.render_pdf_pages_to_png",
        fake_render_pages,
    )
    monkeypatch.setattr(
        "document_processing_pipeline.llm.gemini_client.GeminiClient.generate_json",
        fake_generate_json,
    )

    client = TestClient(app)
    response = client.post(
        "/api/process",
        data={"claim_id": "claim-7"},
        files={"file": ("sample.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["claim_id"] == "claim-7"
    assert body["id_data"]["patient_name"] == "Jane"
    assert body["itemized_bill_data"]["computed_total"] == 99.0
    assert body["metadata"]["page_count"] == 3


def test_process_endpoint_returns_503_when_segregator_unavailable(monkeypatch):
    def fake_extract_pages(_bytes: bytes):
        return [PagePayload(page_number=1, text="Some page")]

    def fake_render_pages(_bytes: bytes):
        return {}

    def fake_generate_json(self, prompt: str, media_parts=None):
        if "classifier" in prompt:
            return {}
        return {}

    monkeypatch.setattr(
        "document_processing_pipeline.api.process.extract_pages_from_pdf",
        fake_extract_pages,
    )
    monkeypatch.setattr(
        "document_processing_pipeline.api.process.render_pdf_pages_to_png",
        fake_render_pages,
    )
    monkeypatch.setattr(
        "document_processing_pipeline.llm.gemini_client.GeminiClient.generate_json",
        fake_generate_json,
    )

    client = TestClient(app)
    response = client.post(
        "/api/process",
        data={"claim_id": "claim-503"},
        files={"file": ("sample.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "upstream_model_unavailable"
