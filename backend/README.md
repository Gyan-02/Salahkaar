# Benefits Readiness Navigator — backend

This backend distinguishes likely program eligibility from operational readiness to apply. Phases 1–8 are implemented. Automated tests and the optional RAG layer remain behind the requested review gates.

## MVP boundaries

The hackathon build is a single-user local demo. It has no authentication, login, registration, RBAC, OAuth, SSO, or multi-tenancy. Only `Document`, `CitizenProfile`, and `Analysis` are persisted.

Uploaded PDFs/images live temporarily under `UPLOAD_PATH` (default: `backend/uploads`). After extraction, the route layer must delete the source upload in a `finally` block. Only extracted structured JSON and analysis results may be persisted. This minimizes retained sensitive material; the structured fields can still contain personal data and must be handled accordingly.

# USER_ACTION_REQUIRED

Cloud object storage requires an explicit later design decision covering provider, encryption, retention, deletion, access control, and consent. It is not part of this MVP.

# FUTURE_EXTENSION

A user model and ownership relationships can be added if the product later introduces authentication or multi-user storage.

## Configuration

Copy `.env.example` to `.env` and set the environment values. `DATABASE_URL` and `UPLOAD_PATH` are required for the running API. `GEMINI_API_KEY` is required only when Gemini extraction is enabled.

# ENV_REQUIRED

- `DATABASE_URL`
- `UPLOAD_PATH`
- `GEMINI_API_KEY` when `USE_GEMINI_EXTRACTOR=true`

`MockExtractor` remains active for deterministic JSON fixtures and demo cases. Real PDF/JPEG/PNG/WebP uploads use `GeminiExtractor` only when both `GEMINI_API_KEY` is configured and `USE_GEMINI_EXTRACTOR=true`. Live extraction uses the configured `GEMINI_MODEL`, requests schema-constrained JSON, and rejects unsupported document types or provider failures clearly.

## Database setup

From `backend`, install `requirements.txt`, create the PostgreSQL database named by `DATABASE_URL`, then run `alembic upgrade head`.

Repository writes are transaction-neutral: callers use `UnitOfWork` or explicitly commit/roll back a session. This keeps multi-record analysis persistence atomic.

## Run the API

From `backend`, run `uvicorn app.main:app --reload`. This is the single application entry point for analysis and grounded guideline retrieval. Interactive OpenAPI documentation is available at `/docs`.

`POST /analysis/run` accepts reviewed structured fields and keeps the deterministic `MockExtractor` path. `POST /documents/upload` accepts supported files up to `MAX_UPLOAD_BYTES`; `POST /documents/extract` requires explicit external-processing consent before invoking Gemini. Uploaded bytes are deleted after extraction in a `finally` block, and abandoned temporary files are removed at application startup and shutdown. The frontend places extracted values into editable fields before analysis.

## Program data safety

# OFFICIAL_SOURCE_REQUIRED

`app/data/programs.json` contains only rules traceable to the supplied official-page or official-guideline text. PM-KISAN and NMMSS are marked `partially_verified`: a verified failure can produce `eligible: false`, but passing the known rules remains `eligible: null` until the missing primary clauses are supplied. PM-JAY is locked to `OFFICIAL_RULES_PENDING`; SECC 2011 is metadata only and no eligibility, readiness, risk, or action result is computed. See `source_audit.json` and `OFFICIAL_SOURCE_CHECKLIST.md`.

Enabled rules cannot contain `PLACEHOLDER` or `# OFFICIAL_SOURCE_REQUIRED`. Unresolved values remain in `official_requirements` and cannot affect an eligibility result.

Readiness score weights are clearly labeled as MVP product heuristics; they are not government policy. Mock cases contain synthetic people and are not evidence of official program rules.

## Current review gate

Phases completed: project/config/data structure, SQLAlchemy models, Pydantic schemas, initial Alembic migration, repositories/unit of work, deterministic Mock extraction, opt-in Gemini document extraction, and all eight configuration-driven business engines.

Phases 8 and 9 are complete: the FastAPI surface uses one shared Mock-only pipeline, and the automated suite covers engines, extraction, API contracts, persistence, demos, the PM-KISAN vertical slice, PM-JAY pending behavior, and a guarded real-PostgreSQL migration round trip.

Run the complete suite with `python -m pytest -q`. To include the real PostgreSQL migration round trip, set `TEST_POSTGRES_URL` to a disposable PostgreSQL database whose name contains `test`; otherwise that one test is safely skipped.

Date normalization is not yet implemented. See `TRACKED_TODOS.md`; no PM-KISAN land-cutoff rule may be enabled until canonical date normalization and the official cutoff/inheritance policy are both verified.

Top-level analysis responses and `/risk/check` expose `risk_reason` as a structured value: `POLICY_INCOMPLETE`, `DOCUMENT_BLOCKERS`, `ELIGIBILITY_FAILURE`, `MULTIPLE_FACTORS`, or `null`. Multiple issues in one category do not produce `MULTIPLE_FACTORS`; it requires two or more distinct categories. Programs in `OFFICIAL_RULES_PENDING` always return `risk_level: PENDING` with `risk_reason: POLICY_INCOMPLETE`.

## Grounded guideline retrieval (Phase 10a)

Run `python -m app.rag.ingestion` to rebuild the locked ChromaDB collection, then run the normal `uvicorn app.main:app --reload` process. `POST /guidelines/lookup` returns ordered source chunks exactly as stored; it does not summarize them or provide open-ended chat. If no chunk passes both lexical evidence and `RAG_MIN_RELEVANCE`, it returns `{"result": null, "status": "NO_OFFICIAL_SOURCE_MATCH"}`.

`app.main` is the final Phase 10 composition root and exposes one FastAPI application, one OpenAPI document, and one backend process. Earlier engines and services still do not import the RAG layer.

## Grounded issue evidence (Phase 10b)

For PM-KISAN and NMMSS, mapped analysis issues may include an additive `official_reference` containing the exact retrieved text, source URL, section reference, and score. Issue-to-query mappings and required claim-support concepts are explicit in `app/rag/evidence.py`; no query or support test is generated or guessed. A chunk must pass both the unchanged `0.35` retrieval floor and the issue-specific claim-support gate. Unmapped, weak, or merely topical results return `official_reference: null`. PM-JAY never invokes analysis-time RAG and always returns a null reference while its rules remain pending. Existing explanation strings and all eligibility, readiness, risk, and action behavior remain unchanged.
