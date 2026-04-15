from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

DocumentType = Literal[
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


class PagePayload(BaseModel):
    page_number: int = Field(ge=1)
    text: str
    image_available: bool = False


class SegregationResult(BaseModel):
    page_number: int = Field(ge=1)
    document_type: DocumentType


class IdentityData(BaseModel):
    patient_name: str | None = None
    date_of_birth: str | None = None
    id_numbers: list[str] = Field(default_factory=list)
    policy_details: str | None = None


class DischargeSummaryData(BaseModel):
    diagnosis: str | None = None
    admit_date: str | None = None
    discharge_date: str | None = None
    physician_details: str | None = None


class BillLineItem(BaseModel):
    description: str
    amount: float = Field(ge=0)


class ItemizedBillData(BaseModel):
    line_items: list[BillLineItem] = Field(default_factory=list)
    reported_total: float | None = Field(default=None, ge=0)
    computed_total: float = Field(0, ge=0)


class ProcessResponse(BaseModel):
    claim_id: str
    id_data: IdentityData
    discharge_summary_data: DischargeSummaryData
    itemized_bill_data: ItemizedBillData
    page_classification: list[SegregationResult]
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
