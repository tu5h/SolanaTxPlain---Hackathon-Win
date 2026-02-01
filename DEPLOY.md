# Deployment

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

## Deploy backend to a host

1. Push repo to GitHub (include `SolanaTxPlain` folder with `backend/`, `frontend/`, `backend/requirements.txt`).

2. Use any host that runs Python (e.g. Railway, Render, Fly.io, VPS, or your provider):
   - **Type:** Web service
   - **Build:** `pip install -r backend/requirements.txt`
   - **Run:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` (use `PORT` from the host; many use 8080)
   - **Env vars:** `GEMINI_API_KEY`; optionally `OPENROUTER_API_KEY` for fallback when Gemini returns 429.

3. Set the frontend’s API base to your deployed backend URL (or serve the frontend from the same origin).

---

## API (README)

- **POST /explain** — Input: `{ "tx_hash": "...", "simple_mode": true, "network": "mainnet" | "devnet" }`  
  Output: `{ summary, intent, wallet_changes, fees, risk_flags, explanation, network }`

- **GET /live/stream?wallet=...&network=mainnet|devnet** — SSE stream of live activity (grouped txs + AI explanation)

- **GET /health** — `{ "status": "ok" }`
