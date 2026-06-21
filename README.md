# Salahkaar

Salahkaar is a local, single-user benefits-readiness demonstration for Bihar. The React frontend presents the existing FastAPI analysis and grounded-guideline contracts without inferring eligibility from missing policy data.

## Run locally

1. Configure and start the backend from `backend`:

   ```powershell
   Copy-Item .env.example .env
   .\.venv\Scripts\python.exe -m alembic upgrade head
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
   ```

   For real document extraction, set `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-2.5-flash`, and `USE_GEMINI_EXTRACTOR=true` in `backend/.env`. Uploaded documents are sent to Google Gemini only after the user checks the consent box; temporary local bytes are deleted after extraction.

2. In the repository root, start the frontend:

   ```powershell
   npm install
   npm run dev
   ```

3. Open `http://127.0.0.1:5173`.

The development server proxies `/api` to `http://127.0.0.1:8000`. Set `VITE_API_BASE_URL` when the API is hosted elsewhere.

## Checks

```powershell
npm run typecheck
npm test
npm run build
npm run format
```

The frontend contains no eligibility thresholds or scoring logic. Scheme decisions, readiness, risk, actions, explanations, and official-source evidence are rendered from backend responses.
