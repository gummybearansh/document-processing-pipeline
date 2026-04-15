from document_processing_pipeline.graph.nodes.segregator import segregator_node
from document_processing_pipeline.schemas.contracts import (
    DischargeSummaryData,
    IdentityData,
    ItemizedBillData,
    PagePayload,
)


def test_segregator_routes_only_relevant_pages(monkeypatch):
    def fake_generate_json(self, prompt: str, media_parts=None):
        assert "claim_forms" in prompt
        return {
            "classifications": [
                {"page_number": 1, "document_type": "identity_document"},
                {"page_number": 2, "document_type": "discharge_summary"},
                {"page_number": 3, "document_type": "itemized_bill"},
                {"page_number": 4, "document_type": "other"},
            ]
        }

    monkeypatch.setattr(
        "document_processing_pipeline.llm.gemini_client.GeminiClient.generate_json",
        fake_generate_json,
    )

    state = {
        "claim_id": "c1",
        "pages": [
            PagePayload(page_number=1, text="id page"),
            PagePayload(page_number=2, text="discharge page"),
            PagePayload(page_number=3, text="bill page"),
            PagePayload(page_number=4, text="other page"),
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

    out = segregator_node(state)
    assert [p.page_number for p in out["id_pages"]] == [1]
    assert [p.page_number for p in out["discharge_pages"]] == [2]
    assert [p.page_number for p in out["itemized_bill_pages"]] == [3]


def test_segregator_defaults_unclassified_pages_to_other(monkeypatch):
    def fake_generate_json(self, prompt: str, media_parts=None):
        return {"classifications": [{"page_number": 1, "document_type": "identity_document"}]}

    monkeypatch.setattr(
        "document_processing_pipeline.llm.gemini_client.GeminiClient.generate_json",
        fake_generate_json,
    )

    state = {
        "claim_id": "c2",
        "pages": [
            PagePayload(page_number=1, text="id page"),
            PagePayload(page_number=2, text="unknown page"),
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

    out = segregator_node(state)
    labels_by_page = {item.page_number: item.document_type for item in out["page_classification"]}
    assert labels_by_page[1] == "identity_document"
    assert labels_by_page[2] == "other"
    assert "segregator_missing_page_classification_defaulted_to_other" in out["errors"]
