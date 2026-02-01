# Deploy to DigitalOcean (README)

## Local run (two terminals)

- **Terminal 1 — Backend:** From project root: activate venv, then `python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`
- **Terminal 2 — Frontend:** `python -m http.server 3000 --directory frontend`
- Open **http://localhost:3000** (frontend calls backend at 8000). See [DEV.md](DEV.md).

---

## One-time setup

1. **Virtualenv and deps** (from project root):

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r backend\requirements.txt
   ```

2. **API key:** Copy `.env.example` to `.env` (or `backend/.env`). Set `GEMINI_API_KEY=...` (get key at [Google AI Studio](https://aistudio.google.com/apikey)).

---

## DigitalOcean App Platform

1. Push repo to GitHub (include `SolanaTxPlain` folder with `backend/`, `frontend/`, `backend/requirements.txt`).

2. DigitalOcean → Create → Apps → GitHub → select repo.

3. Configure:
   - **Type:** Web Service
   - **Source directory:** root (or folder that contains `backend/`)
   - **Build command:** `pip install -r backend/requirements.txt` (or `pip install -r requirements.txt` if you put requirements at root)
   - **Run command:** `uvicorn backend.main:app --host 0.0.0.0 --port 8080`
   - **HTTP port:** 8080

4. **Environment variables:** Add `GEMINI_API_KEY`. Optionally `OPENROUTER_API_KEY` for fallback when Gemini returns 429.

5. Deploy. Public URL: e.g. `https://your-app-xxxxx.ondigitalocean.app`.

---

## API (README)

- **POST /explain** — Input: `{ "tx_hash": "...", "simple_mode": true }`  
  Output: `{ summary, intent, wallet_changes, fees, risk_flags, explanation }`

- **GET /health** — `{ "status": "ok" }`
