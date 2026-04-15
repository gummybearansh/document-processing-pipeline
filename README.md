# Claim Processing Pipeline

FastAPI + LangGraph service for processing medical claim PDFs with page-level segregation and multi-agent extraction.

This implementation is aligned to the assignment workflow:

- `START -> Segregator Agent -> [ID Agent, Discharge Summary Agent, Itemized Bill Agent] -> Aggregator -> END`

## Development Approach: TDD First

This repository is intentionally built with a test-driven workflow:

- write failing tests first for each behavior (`Red`)
- implement the smallest change to make tests pass (`Green`)
- clean up code while preserving test guarantees (`Refactor`)

Core rule for changes:

- no new behavior is considered complete without:
  - unit coverage for node-level logic
  - integration coverage for graph behavior
  - e2e coverage for API-level contract

## What This Project Does

- Accepts a claim PDF and `claim_id` via API.
- Classifies each page into one of the required 9 document types.
- Routes only relevant pages to each extraction agent.
- Extracts:
  - identity information
  - discharge summary information
  - itemized bill rows + totals
- Returns unified JSON response with metadata and error context.

## Required Document Types

Segregator classifies each page into exactly one:

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

- Python 3.11+
- `uv` (dependency + environment management)
- FastAPI
- LangGraph
- Gemini (`gemini-2.5-flash`)
- `pypdf` (text extraction)
- `pymupdf` (page image rendering for scanned PDFs)
- Pytest (`unit`, `integration`, `e2e`)

## Repository Structure

```text
src/document_processing_pipeline/
  api/process.py
  graph/
    workflow.py
    state.py
    nodes/
      segregator.py
      id_agent.py
      discharge_agent.py
      itemized_bill_agent.py
      aggregator.py
  llm/gemini_client.py
  schemas/contracts.py
  services/pdf_text_extractor.py
tests/
  unit/
  integration/
  e2e/
docs/
  video-walkthrough-script.md
  architecture-and-internals.md
```

## API

### `POST /api/process`

Consumes `multipart/form-data`:

- `claim_id`: string
- `file`: PDF

Success response (`200`) includes:

- `claim_id`
- `id_data`
- `discharge_summary_data`
- `itemized_bill_data`
- `page_classification`
- `errors`
- `metadata`

Failure behavior:

- `400`: invalid input (non-PDF / empty PDF)
- `503`: `upstream_model_unavailable` when segregator cannot produce usable classifications

## Example Request

```bash
curl -X POST "http://127.0.0.1:8000/api/process" \
  -F "claim_id=claim-001" \
  -F "file=@final_image_protected.pdf;type=application/pdf"
```

## Local Development

### 1) Install dependencies

```bash
uv sync
```

### 2) Configure environment

```bash
cp .env.example .env
```

Set:

- `GEMINI_API_KEY=...`
- `GEMINI_MODEL=gemini-2.5-flash`
- `APP_ENV=development`

### 3) Run API

```bash
uv run uvicorn document_processing_pipeline.main:app --reload
```

API base URL:

- `http://127.0.0.1:8000`

Health endpoint:

- `GET /healthz`

## TDD and Test Suite

Run all tests:

```bash
uv run pytest -q
```

Run by layer:

```bash
uv run pytest tests/unit -q
uv run pytest tests/integration -q
uv run pytest tests/e2e -q
```

Coverage run:

```bash
uv run pytest --cov=src/document_processing_pipeline --cov-report=term-missing
```

Current suite validates:

- segregator routing and fallback invariants
- graph-level orchestration
- API contract behavior
- 503 behavior when segregator is unavailable

Recommended dev loop:

1. add/adjust tests for the requirement
2. run targeted tests
3. implement minimal code change
4. run full suite (`uv run pytest -q`)
5. refactor only with tests green

## Notes on Extraction Quality

- For scanned/image-heavy PDFs, page images are passed to Gemini.
- Itemized bill extraction currently computes row sum as `computed_total`.
- If `reported_total` differs from `computed_total`, summary-level charges (tax/fees/adjustments) may not have been captured as item rows yet.

## Deployment (Render)

`render.yaml` is included.

Minimal setup:

1. Create Render web service from repo.
2. Ensure environment variable is set:
   - `GEMINI_API_KEY`
3. Deploy.

Default commands from `render.yaml`:

- Build: `pip install uv && uv sync --frozen`
- Start: `uv run uvicorn document_processing_pipeline.main:app --host 0.0.0.0 --port $PORT`

## Demo/Submission Aids

- Deep internals + architecture:
  - `docs/architecture-and-internals.md`
