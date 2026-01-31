# Run locally & deploy to DigitalOcean

## Run locally

1. **Create a virtualenv and install deps** (from repo root `SolanaTxPlain/`):

   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate   # macOS/Linux
   pip install -r requirements.txt
   ```

2. **Set your Gemini API key** (get one at [Google AI Studio](https://aistudio.google.com/apikey)):

   - Copy `.env.example` to `.env`
   - Set `GEMINI_API_KEY=...` in `.env`

3. **Start the app** (from `SolanaTxPlain/`):

   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. Open **http://localhost:8000** — paste a Solana mainnet transaction hash and click **Explain**.

---

## Deploy to DigitalOcean App Platform

1. **Push this repo to GitHub** (only the `SolanaTxPlain` folder or the whole repo).

2. **In DigitalOcean:** Create → Apps → Create App → GitHub → select repo and branch.

3. **Configure the app:**
   - **Type:** Web Service
   - **Source:** your repo root (where `requirements.txt` and `backend/` live)
   - **Build command:** `pip install -r requirements.txt`
   - **Run command:** `uvicorn backend.main:app --host 0.0.0.0 --port 8080`
   - **HTTP port:** 8080 (or whatever you set in run command)

4. **Environment variables:** Add in the DO dashboard:
   - `GEMINI_API_KEY` = your Gemini API key

5. **Deploy.** Your app URL will be something like `https://your-app-xxxxx.ondigitalocean.app`.

6. Open the URL — users can paste a transaction hash and get an explanation online.

---

## Notes

- The app serves the frontend at `/` and the API at `POST /explain` and `GET /health`.
- Solana data comes from the public RPC `https://api.mainnet-beta.solana.com`. For heavier use, switch to a dedicated RPC (e.g. Helius) and set its URL in env.
