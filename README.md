# Salahkaar

## AI-Powered Benefits Readiness Assistant

Salahkaar is a citizen-facing readiness assistant that helps applicants identify problems in their documents and application information before applying for government welfare schemes.

Built as a demonstration for Bihar, Salahkaar combines consent-based AI document extraction, deterministic readiness analysis, contradiction detection, corrective action planning, and grounded official-guideline retrieval in one workflow.

Instead of answering only **“Am I eligible?”**, Salahkaar focuses on the practical question:

> **“Is my application ready?”**

Salahkaar is not an official government portal and does not make approval decisions.

## The Problem

Applications can be delayed or rejected even when a citizen may satisfy a scheme’s rules. Common operational problems include:

- Names that differ across identity, bank, or land records
- Expired certificates
- Missing application information
- Contradictory family or address records
- Bank-account inconsistencies
- Unverified or incomplete policy coverage

These problems are often discovered only after submission. Salahkaar surfaces them earlier and explains what the applicant can correct.

## Core Features

### 1. Consent-Based AI Document Extraction

Citizens can upload PDF, JPEG, PNG, or WebP documents and extract supported fields using Google Gemini.

- External processing requires explicit user consent.
- Gemini receives a schema-constrained extraction request.
- Only predefined fields are accepted.
- Missing values remain unknown instead of being fabricated.
- Extracted dates must be valid ISO-8601 values or are treated as unknown.
- Every extracted value remains editable before analysis.
- Temporary local upload bytes are deleted after extraction, including failure paths.
- Uploaded files are limited to the configured size, 10 MB by default.

The deterministic mock extractor remains available for automated tests and prepared demo cases.

### 2. Readiness and Contradiction Analysis

The backend evaluates reviewed information using deterministic, configuration-driven engines. It can identify:

- Cross-document name mismatches
- Address differences, while ignoring harmless punctuation differences
- Bank-account-holder mismatches
- Expired documents
- Missing required answers
- Failed enabled eligibility rules
- Low document-quality signals

Results can include:

- Eligibility state, including an explicit unknown state
- Application readiness score
- Structured risk level and risk reason
- Detected issues and supporting document evidence
- Prioritized corrective actions
- Follow-up questions
- Human-readable score deductions

Readiness is not presented as an eligibility probability.

### 3. Grounded Official-Guideline Retrieval

The guideline lookup is a retrieval tool, not a general chatbot. It returns exact passages from the locked source corpus with:

- Original source text
- Official source URL
- Section or clause reference
- Retrieval date and source status
- Relevance score in technical details

Returned passages are ordered but never merged, summarized, or rewritten.

If no passage meets the relevance threshold, the API returns:

```json
{
  "result": null,
  "status": "NO_OFFICIAL_SOURCE_MATCH"
}
```

### 4. Claim-Support Validation

Retrieval relevance alone is not treated as proof that a passage supports a blocker. Evidence attachment uses an additional issue-specific claim-support gate.

If a passage is merely topically related, `official_reference` remains `null`. This prevents a general bank-account passage, for example, from being presented as proof of a specific name-matching requirement.

### 5. Responsible Uncertainty

Salahkaar does not convert missing policy data into a positive or negative decision.

When complete verified criteria are unavailable, the system communicates that limitation using structured states rather than requiring the frontend to interpret explanation text.

## Supported Programs

| Program                | Current assessment behavior                                                                                                                                                       |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PM-KISAN               | Enabled verified rules can produce a failure. Passing the currently enabled rules remains non-final while policy coverage is incomplete.                                          |
| NMMSS                  | Enabled verified rules and document checks are evaluated. Passing rules do not become a fabricated final eligibility decision.                                                    |
| Ayushman Bharat PM-JAY | Intentionally returns `OFFICIAL_RULES_PENDING`; national source context is available for lookup, but incomplete Bihar-specific policy coverage is not used to invent eligibility. |

PM-JAY’s pending contract is:

```json
{
  "status": "OFFICIAL_RULES_PENDING",
  "eligible": null,
  "readiness_score": null,
  "risk_level": "PENDING",
  "risk_reason": "POLICY_INCOMPLETE",
  "blockers": [],
  "actions": []
}
```

## Structured Risk Reasons

The frontend uses `risk_reason` directly and never derives product behavior by parsing explanation strings.

- `POLICY_INCOMPLETE`
- `DOCUMENT_BLOCKERS`
- `ELIGIBILITY_FAILURE`
- `MULTIPLE_FACTORS`

`MULTIPLE_FACTORS` means multiple risk categories apply, not merely multiple issues inside one category.

## User Workflow

1. **Select a scheme** — Choose PM-KISAN, NMMSS, or PM-JAY.
2. **Answer scheme questions** — Required answers are validated before review.
3. **Upload or enter document information** — Use Gemini extraction or enter fields manually.
4. **Review extracted fields** — Correct values before they enter the analysis pipeline.
5. **Run readiness analysis** — Evaluate enabled rules, contradictions, missing data, and document signals.
6. **Review results** — See readiness, risk reason, issues, evidence, questions, and corrective actions.
7. **Explore official guidance** — Retrieve exact source passages through the grounded lookup.

## Architecture

```text
React + TypeScript frontend
          |
          v
Single FastAPI application
          |
          +-- Upload lifecycle and Gemini extraction
          +-- Profile builder
          +-- Program registry and eligibility engine
          +-- Contradiction engine
          +-- Readiness and risk engines
          +-- Action planner and explanation engine
          +-- ChromaDB guideline retrieval
          |
          v
PostgreSQL persistence
```

The backend exposes one FastAPI application, one OpenAPI document, and one deployment process. Adding a new scheme is designed to be data-driven through `backend/app/data/*.json`, without adding scheme-specific branches to the core engines.

## Technology Stack

### Frontend

- React
- TypeScript
- Vite
- React Router
- Lucide icons
- Vitest and Testing Library

### Backend

- Python
- FastAPI and OpenAPI
- Pydantic
- SQLAlchemy and Alembic
- PostgreSQL
- Pytest

### AI and Retrieval

- Google Gemini 2.5 Flash for structured document extraction
- ChromaDB for persistent grounded retrieval
- Deterministic local embeddings for the locked demo corpus
- Explicit retrieval confidence and claim-support gates

## Project Structure

```text
Salahkaar/
├── src/                         # React frontend
│   ├── components/
│   ├── pages/
│   ├── test/
│   ├── api.ts
│   ├── config.ts
│   └── types.ts
├── backend/
│   ├── alembic/                 # Database migrations
│   ├── app/
│   │   ├── api/                 # FastAPI routes and pipeline
│   │   ├── data/                # Program, rule, source, and RAG data
│   │   ├── engines/             # Deterministic assessment engines
│   │   ├── models/              # SQLAlchemy models
│   │   ├── rag/                 # ChromaDB ingestion and retrieval
│   │   ├── repositories/
│   │   ├── schemas/
│   │   └── services/extraction/ # Mock and Gemini extractors
│   └── tests/
├── output/pdf/                  # Locally generated synthetic demo documents
├── package.json
└── vite.config.ts
```

## Local Development

### Prerequisites

- Node.js and npm
- Python 3.11 or newer
- PostgreSQL
- Gemini API key only when live document extraction is enabled

### Backend

From `backend`:

```powershell
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Configure `backend/.env`:

```dotenv
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/benefits_readiness
UPLOAD_PATH=./uploads

GEMINI_API_KEY=YOUR_API_KEY
GEMINI_MODEL=gemini-2.5-flash
USE_GEMINI_EXTRACTOR=true
GEMINI_TIMEOUT_SECONDS=30
MAX_UPLOAD_BYTES=10485760

CHROMA_PATH=./chroma_data
RAG_MIN_RELEVANCE=0.35
RAG_TOP_N=3
```

Never commit `backend/.env` or expose the Gemini API key in frontend variables.

The API is available at:

- API: `http://127.0.0.1:8000`
- OpenAPI UI: `http://127.0.0.1:8000/docs`

### Frontend

From the repository root:

```powershell
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

Local development uses Vite’s `/api` proxy to reach `http://127.0.0.1:8000`. For a hosted frontend, configure:

```dotenv
VITE_API_BASE_URL=https://your-backend.example.com
```

`VITE_*` values are public browser configuration and must never contain secrets.

## Useful API Endpoints

| Endpoint                   | Purpose                              |
| -------------------------- | ------------------------------------ |
| `GET /health`              | Service health                       |
| `GET /programs`            | Supported program definitions        |
| `POST /documents/upload`   | Temporary PDF/image upload           |
| `POST /documents/extract`  | Consent-gated document extraction    |
| `POST /analysis/run`       | Complete readiness-analysis pipeline |
| `POST /demo/run/{case_id}` | Prepared synthetic demo cases        |
| `POST /guidelines/lookup`  | Exact official-source retrieval      |

Additional engine-specific endpoints are documented in OpenAPI.

## Testing and Verification

### Frontend

```powershell
npm run typecheck
npm test
npm run build
npm run format
```

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

The guarded PostgreSQL migration test requires `TEST_POSTGRES_URL` to reference a disposable database whose name contains `test`. It is skipped when that variable is absent.

## Deployment

The frontend can be deployed to Vercel and the backend to a Python-compatible service such as Render.

For Vercel, configure `VITE_API_BASE_URL` in Project Settings instead of committing environment-specific files. Generated `node_modules` and `dist` directories must not be committed.

For the backend, configure PostgreSQL, upload-path, Gemini, and Chroma variables in the hosting environment. The current upload lifecycle uses local temporary storage and is intended for this MVP; durable cloud document storage is deliberately out of scope.

## Privacy and Security Boundaries

- No authentication or multi-user tenancy is included in this MVP.
- Uploaded bytes are temporary and are deleted after extraction.
- Extracted structured fields and analysis results may still contain personal information.
- Real documents are sent to Gemini only after explicit consent.
- API keys remain backend-only.
- Synthetic demo documents are prominently marked `SYNTHETIC DEMO - NOT VALID`.
- Cloud retention, encryption, deletion, and access-control policies require a separate production design.

## Responsible AI Principles

> **If sufficient evidence is unavailable, the system should say so.**

Salahkaar does not:

- Invent final eligibility decisions
- Fabricate missing document information
- Generate unsupported policy rules
- Present weak topical retrieval as proof of a specific claim
- Hide policy incompleteness from users

## Extending Salahkaar

Program logic is configuration-driven. To add or update a scheme, review the files under `backend/app/data/`, including:

- `programs.json`
- `document_schemas.json`
- `contradictions.json`
- `readiness_rules.json`
- `actions.json`
- `source_audit.json`
- `rag_corpus.json`

Every active rule must be backed by a verified source. Unresolved values remain marked for official-source verification and must not influence active eligibility decisions.

## Disclaimer

Salahkaar is a demonstration project. It is not affiliated with or endorsed by any government authority, does not submit applications, and does not provide final approval or eligibility decisions.

Its purpose is to help citizens review information, identify potential readiness problems, understand corrective actions, and inspect supporting official-source passages before applying through the appropriate government channel.
