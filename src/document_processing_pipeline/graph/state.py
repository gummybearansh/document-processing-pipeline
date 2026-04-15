from __future__ import annotations

from typing import Any, TypedDict

from document_processing_pipeline.schemas.contracts import (
    DischargeSummaryData,
    IdentityData,
    ItemizedBillData,
    PagePayload,
    SegregationResult,
)


class ClaimGraphState(TypedDict):
    claim_id: str
    pages: list[PagePayload]
    page_images: dict[int, bytes]
    page_classification: list[SegregationResult]
    id_pages: list[PagePayload]
    discharge_pages: list[PagePayload]
    itemized_bill_pages: list[PagePayload]
    id_data: IdentityData
    discharge_summary_data: DischargeSummaryData
    itemized_bill_data: ItemizedBillData
    errors: list[str]
    metadata: dict[str, Any]
    final_output: dict[str, Any]
