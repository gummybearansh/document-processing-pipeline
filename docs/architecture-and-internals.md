# Architecture and Internals

This document is the technical deep dive for understanding and explaining the project.

## 1) Objective

Process a claim PDF and return structured JSON by enforcing this sequence:

1. Segregate pages into required document types.
2. Route only relevant pages to 3 extraction agents.
3. Aggregate all extracted outputs into one API response.

## 2) Component Architecture

- **API Layer**
  - `FastAPI` endpoint in `src/document_processing_pipeline/api/process.py`
  - validates input and orchestrates graph invocation

- **Preprocessing Layer**
  - text extraction via `pypdf`
  - page image rendering via `pymupdf` for scanned/image-heavy PDFs

- **Orchestration Layer**
  - LangGraph workflow in `src/document_processing_pipeline/graph/workflow.py`
  - shared graph state in `src/document_processing_pipeline/graph/state.py`

- **LLM Client Layer**
  - Gemini wrapper in `src/document_processing_pipeline/llm/gemini_client.py`
  - JSON parsing resilience for fenced/embedded model outputs

- **Agent Nodes**
  - Segregator node
  - ID extraction node
  - Discharge summary extraction node
  - Itemized bill extraction node
  - Aggregator node

## 3) Runtime Data Flow

1. `POST /api/process` receives `claim_id` + PDF.
2. PDF -> `pages` (text) and `page_images` (PNG bytes).
3. Initial graph state is created.
4. Segregator classifies pages into one of 9 document types.
5. Segregator emits route lists for `id_pages`, `discharge_pages`, `itemized_bill_pages`.
6. Each extraction agent runs only on its routed pages.
7. Aggregator combines node outputs into `final_output`.
8. API returns validated `ProcessResponse`.

## 4) Assignment Workflow Mapping

Actual graph edges:

- `START -> segregator`
- `segregator -> id_agent`
- `segregator -> discharge_summary_agent`
- `segregator -> itemized_bill_agent`
- `id_agent -> aggregator`
- `discharge_summary_agent -> aggregator`
- `itemized_bill_agent -> aggregator`
- `aggregator -> END`

This enforces the assignment rule that segregation and routing are explicit and extraction agents are scoped to subsets.

## 5) Segregator Node Internals

File: `src/document_processing_pipeline/graph/nodes/segregator.py`

Segregator outputs labels in this exact domain:

- `claim_forms`
- `cheque_or_bank_details`
- `identity_document`
- `itemized_bill`
- `discharge_summary`
- `prescription`
- `investigation_report`
- `cash_receipt`
- `other`

Implementation details:

- Uses multimodal Gemini input:
  - page image content
  - text hints where available
- Validates each returned classification item.
- Builds route arrays for 3 extractors.
- If classifier output is empty/unusable, it raises `upstream_model_unavailable`.

## 6) Extraction Nodes Internals

## 6.1 ID Agent

File: `src/document_processing_pipeline/graph/nodes/id_agent.py`

- Input: `id_pages` only
- Output:
  - `patient_name`
  - `date_of_birth`
  - `id_numbers`
  - `policy_details`
- Normalization:
  - coerces `id_numbers` string -> list

## 6.2 Discharge Summary Agent

File: `src/document_processing_pipeline/graph/nodes/discharge_agent.py`

- Input: `discharge_pages` only
- Output:
  - `diagnosis`
  - `admit_date`
  - `discharge_date`
  - `physician_details`

## 6.3 Itemized Bill Agent

File: `src/document_processing_pipeline/graph/nodes/itemized_bill_agent.py`

- Input: `itemized_bill_pages` only
- Output:
  - `line_items[]` (`description`, `amount`)
  - `reported_total`
  - `computed_total`
- `computed_total` is deterministic sum of extracted row amounts.
- Current known gap: summary-level charges (tax/fees) may not always appear in `line_items`, creating deltas.

## 7) Aggregator Node Internals

File: `src/document_processing_pipeline/graph/nodes/aggregator.py`

Aggregates:

- `claim_id`
- `id_data`
- `discharge_summary_data`
- `itemized_bill_data`
- `page_classification`
- `errors`
- `metadata`

Returned object becomes API response payload.

## 8) Failure and Reliability Model

## 8.1 Segregator failure behavior

If segregator cannot produce usable classifications:

- graph raises `RuntimeError("upstream_model_unavailable")`
- API maps this to:
  - HTTP `503`
  - body detail: `upstream_model_unavailable`

This prevents fake "all-other" successful responses.

## 8.2 Upstream model limits

Gemini free-tier can return:

- `429 RESOURCE_EXHAUSTED` (quota)
- `503 UNAVAILABLE` (high demand)

During these windows, endpoint can validly return 503 if segregator is unavailable.

## 9) Bill Reconciliation Analysis

Observed extraction on sample file:

- `reported_total = 6625.0`
- `computed_total = 6329.3`
- delta = `295.7`

Likely cause:

- one or more summary-only financial lines (tax/service/adjustments) contribute to final total but are outside extracted row set.

Consequence:

- row extraction is mostly correct,
- but full accounting reconciliation requires explicit extraction of summary-level amounts.

## 10) Test Strategy (TDD)

Current coverage layers:

- **Unit**:
  - segregator routing + fallback behavior
  - aggregator assembly
  - Gemini JSON parser resilience
- **Integration**:
  - full graph invocation
- **E2E**:
  - API happy path
  - API 503 path for segregator unavailability

Goal of suite:

- protect workflow invariants while allowing model/prompt iteration.

## 11) Next Technical Improvements

1. Add bill reconciliation schema fields:
   - `delta`
   - `reconciliation_status`
2. Extract `summary_lines` in bill agent (tax/fees/discounts/subtotals).
3. Add retry-with-backoff around segregator model call.
4. Add `metadata.failed_nodes` and `metadata.model_status`.
5. Add fixture-based regression tests for known bill layouts.
