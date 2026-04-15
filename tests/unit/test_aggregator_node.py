from document_processing_pipeline.graph.nodes.aggregator import aggregator_node
from document_processing_pipeline.schemas.contracts import (
    DischargeSummaryData,
    IdentityData,
    ItemizedBillData,
)


def test_aggregator_merges_all_agent_outputs():
    state = {
        "claim_id": "claim-1",
        "pages": [],
        "page_classification": [],
        "id_pages": [],
        "discharge_pages": [],
        "itemized_bill_pages": [],
        "id_data": IdentityData(patient_name="John"),
        "discharge_summary_data": DischargeSummaryData(diagnosis="Fever"),
        "itemized_bill_data": ItemizedBillData(reported_total=500.0, computed_total=500.0),
        "errors": [],
        "metadata": {"source": "test"},
        "final_output": {},
    }
    out = aggregator_node(state)
    assert out["final_output"]["claim_id"] == "claim-1"
    assert out["final_output"]["id_data"]["patient_name"] == "John"
    assert out["final_output"]["metadata"]["source"] == "test"
