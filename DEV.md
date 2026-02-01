# Local development (README architecture)

Frontend and backend run as **two separate processes**. Run all commands from **project root** (folder containing `backend/`, `frontend/`, `.venv/`).

---

## 1. Backend (API only)

**Terminal 1** — from project root:

```powershell
cd "\SolanaTxPlain"
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

- API: **http://localhost:8000**
- Endpoints: `GET /health`, `POST /explain` (body: `{ "tx_hash": "...", "simple_mode": true, "network": "mainnet" | "devnet" }`), `GET /live/stream?wallet=...&network=mainnet|devnet` (SSE), `GET /docs`
- Set `GEMINI_API_KEY` in `backend/.env` or project root `.env` (copy from `.env.example`).

---

## 2. Frontend (static dev server)

**Terminal 2** — from project root:

```powershell
python -m http.server 3000 --directory frontend
```

- App: **http://localhost:3000**
- Frontend calls backend at `http://localhost:8000` when served on port 3000.

---

## 3. Demo flow (README)

1. Open **http://localhost:3000**
2. Paste transaction hash → Click **Explain**
3. See **Summary**, **Wallet impact**, **Fees**, **Risk notes**, **AI explanation**
4. Toggle **Simple mode** (beginner-friendly vs technical)

---

## Scripts (optional)

If you have a `scripts/` folder: run backend with `.\scripts\run_backend.ps1` and frontend with `.\scripts\run_frontend.ps1` from project root. Otherwise use the commands in sections 1 and 2 above.

---

## Troubleshooting

| Problem | Fix |
|--------|-----|
| **No module named uvicorn** | Activate venv from project root: `.\.venv\Scripts\Activate.ps1` then run uvicorn again. |
| **No module named backend** | Run uvicorn from **project root**, not from inside `backend/`. |
| **Backend: not connected** | Start backend on port 8000 first; open frontend at http://localhost:3000 (not file://). |
