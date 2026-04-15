# Claim Processing Pipeline

Production-style FastAPI + LangGraph backend that processes healthcare claim PDFs using page-level segregation and specialized extraction agents.

## Why This Project Stands Out

- **Workflow-driven AI orchestration**: uses a graph-based pipeline, not a single monolithic prompt.
- **Deterministic routing**: each extraction agent receives only relevant pages.
- **Resilient API behavior**: explicit failure handling for upstream model unavailability.
- **TDD-first engineering**: unit, integration, and e2e tests guide implementation.
- **Scanned PDF support**: combines text extraction and image-based understanding.

## Architecture at a Glance

```text
START
  -> Segregator Agent (page classification into 9 doc types)
      -> ID Agent
      -> Discharge Summary Agent
      -> Itemized Bill Agent
          -> Aggregator
              -> END
```

### Core Rule Enforced

The segregator classifies all pages first, then routes subsets.  
Only routed pages are processed by extraction agents.

## What It Extracts

- **Identity data**: patient name, DOB, ID numbers, policy details
- **Discharge summary**: diagnosis, admit/discharge dates, physician
- **Itemized bill**: line items, reported total, computed total
- **Traceability**: page-level classification + processing metadata + explicit errors

## Document Classes

Each page is classified into exactly one of:

- `claim_forms`
- `cheque_or_bank_details`
- `identity_document`
- `itemized_bill`
- `discharge_summary`
- `prescription`
- `investigation_report`
- `cash_receipt`
- `other`

## Tech Stack

- Python 3.11
- `uv` for package/environment management
- FastAPI
- LangGraph
- Gemini (`gemini-2.5-flash`)
- `pypdf` + `pymupdf`
- Pytest

## API

### `POST /api/process`

Consumes `multipart/form-data`:

- `claim_id` (string)
- `file` (PDF)

Returns:

- `id_data`
- `discharge_summary_data`
- `itemized_bill_data`
- `page_classification`
- `errors`
- `metadata`

Failure codes:

- `400` invalid input
- `503` `upstream_model_unavailable` when classifier output is unusable

### Example Request

```bash
curl -X POST "http://127.0.0.1:8000/api/process" \
  -F "claim_id=claim-001" \
  -F "file=@final_image_protected.pdf;type=application/pdf"
```

## Engineering Approach (TDD)

This project is built with a strict red-green-refactor loop:

1. write a failing test for target behavior
2. implement minimal code to pass
3. refactor with tests still green

### Test Layers

- **Unit**: node-level logic (segregation, aggregation, parser robustness)
- **Integration**: full LangGraph workflow behavior
- **E2E**: API contract and failure-path validation

Run all tests:

```bash
uv run pytest -q
```

## Local Setup

```bash
uv sync
cp .env.example .env
uv run uvicorn document_processing_pipeline.main:app --reload
```

Required env vars:

- `GEMINI_API_KEY`
- `GEMINI_MODEL` (default: `gemini-2.5-flash`)
- `APP_ENV`

## Deployment (Render)

This repo includes `render.yaml`.

Default Render commands:

- Build: `pip install uv && uv sync --frozen`
- Start: `uv run uvicorn document_processing_pipeline.main:app --host 0.0.0.0 --port $PORT`

Required Render env var:

- `GEMINI_API_KEY`

## Project Structure

```text
src/document_processing_pipeline/
  api/process.py
  graph/workflow.py
  graph/nodes/
  llm/gemini_client.py
  schemas/contracts.py
  services/pdf_text_extractor.py
tests/
  unit/
  integration/
  e2e/
docs/
  architecture-and-internals.md
```

## Notes

- For scanned PDFs, page images are used for model inference.
- Bill `computed_total` is row-sum based; `reported_total` comes from document totals.
- Deep technical internals are documented in `docs/architecture-and-internals.md`.

## Design Trade-offs

- **Graph-based orchestration vs single prompt**
  - Chosen: LangGraph multi-node pipeline for explicit control and debuggability.
  - Trade-off: more code and state management complexity in exchange for clearer routing, better observability, and easier testing.

- **Specialized extractors vs one general extractor**
  - Chosen: three dedicated extraction agents (ID, Discharge, Itemized Bill).
  - Trade-off: more prompts/schemas to maintain, but significantly better separation of concerns and tighter field-level contracts.

- **Multimodal page processing vs text-only extraction**
  - Chosen: text + rendered page images to support scanned PDFs.
  - Trade-off: higher inference cost/latency compared with text-only, but materially better real-world coverage for insurance documents.

- **Fail-fast `503` on unusable segregation vs silent fallback success**
  - Chosen: return `503 upstream_model_unavailable` when classifier output is unusable.
  - Trade-off: stricter client handling requirements, but prevents false positives and protects downstream data integrity.

- **TDD-first delivery speed vs short-term iteration speed**
  - Chosen: test-first workflow with unit/integration/e2e layers.
  - Trade-off: higher initial implementation overhead, but safer refactors and much higher confidence under model/prompt changes.

- **Schema-constrained output vs flexible free-form extraction**
  - Chosen: Pydantic-validated structured response contracts.
  - Trade-off: occasional coercion/normalization logic required, but improved API stability for consumers and easier regression testing.
