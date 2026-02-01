# SolanaTxPlain — Build Plan

Simple step-by-step plan. Start small, add features as you go.  
Uses: **Gemini AI**, **OpenRouter** (free credits), **DigitalOcean** (free credits).

---

## Phase 1 — Foundation (Backend + Data)

**Goal:** Fetch a Solana transaction and return raw data from your own API.

### Step 1.1 — Project setup
- Create a Python project (e.g. `backend/` or project root).
- Add `requirements.txt`: `fastapi`, `uvicorn`, `httpx` (or `requests`).
- Add a single FastAPI app with one route: `GET /health` → `{"status": "ok"}`.
- Run locally: `uvicorn main:app --reload`. Confirm it works.

### Step 1.2 — Fetch transaction by hash
- Add a function that takes a transaction signature (hash) and calls **Solana RPC** `getTransaction` (public RPC or a free one like Helius/Solscan if you have a key).
- Use **no API key** first: Solana public RPC `https://api.mainnet-beta.solana.com` is enough to start.
- Expose it as something like `GET /tx/{signature}` or `POST /tx` with body `{"tx_hash": "..."}`.
- Return the raw JSON from the RPC (or a simplified version). No parsing yet.

### Step 1.3 — Parse into a simple structure
- From the raw transaction response, extract and return a small structured object, e.g.:
  - `fee` (from meta)
  - `slot` / `blockTime`
  - `account_keys` (or just count)
  - `instructions` (count or brief list)
- Still no AI. Goal: **"Given a tx hash, my API returns clean structured tx info."**

**Checkpoint:** You can paste a real mainnet tx hash and get back fee, time, and basic structure.

---

## Phase 2 — First AI Explanation (Gemini)

**Goal:** Send parsed tx data to Gemini and get a short plain-English summary.

### Step 2.1 — Gemini setup
- Get a Gemini API key (Google AI Studio).
- Add to `requirements.txt`: `google-generativeai` (or use `httpx` to call the REST API).
- In code: load API key from env (e.g. `GEMINI_API_KEY`), create client.

### Step 2.2 — One prompt, one summary
- Build a **single prompt** that includes:
  - The structured tx data (fee, instructions, account keys, etc.).
  - Ask for: "In 1–2 sentences, what did this transaction do?"
- Call Gemini with that prompt; return the model’s text in your API response.

### Step 2.3 — Add `/explain` endpoint
- New route: `POST /explain` with body `{"tx_hash": "..."}`.
- Flow: fetch tx (Step 1.2) → parse (Step 1.3) → send to Gemini (Step 2.2) → return:
  - `summary` (Gemini’s plain-English answer)
  - Optional: `fee`, `slot`, or whatever you already have.

**Checkpoint:** Paste tx hash → API returns a human-readable summary from Gemini.

---

## Phase 3 — Richer Parsing + Wallet Impact

**Goal:** Show what changed for the user (SOL and tokens).

### Step 3.1 — Balance deltas
- From transaction meta, read `preBalances` / `postBalances` and account keys.
- Compute SOL balance change per account (optional: focus on the “main” user account — e.g. first signer).
- Add to your parsed structure: e.g. `sol_change`, or `balance_changes: [{account, before, after, change}]`.

### Step 3.2 — Token balance changes (if available)
- If the RPC response includes token balance info in meta (e.g. `preTokenBalances` / `postTokenBalances`), parse it.
- Add to response: e.g. `token_changes: [{mint, symbol if known, change}]`.
- If not available from public RPC, you can skip or stub; you can add Helius later for better data.

### Step 3.3 — Include in `/explain`
- Pass balance deltas and token changes into the Gemini prompt.
- Ask Gemini to mention wallet impact in the summary (e.g. "You spent 0.5 SOL and received …").
- Return `wallet_changes` (or similar) in the `/explain` response alongside `summary`.

**Checkpoint:** Explanation and response include SOL/token impact.

---

## Phase 4 — Intent + Risk (Still Gemini)

**Goal:** Classify transaction type and add simple risk wording.

### Step 4.1 — Intent
- In the same Gemini call (or a second one), ask: "Classify this transaction: one of SOL transfer, token swap, NFT mint, staking, contract interaction, other."
- Return `intent` in the JSON (e.g. `"token swap"`).

### Step 4.2 — Simple risk note
- Add to prompt: "Is there anything risky or unusual? (unknown program, very high fee, approval, etc.) One short sentence or 'Nothing obvious.'"
- Return `risk_note` in the response.

Keep prompts short; one Gemini call for summary + intent + risk is enough.

**Checkpoint:** `/explain` returns `summary`, `intent`, `risk_note`, `wallet_changes`, `fee`.

---

## Phase 5 — OpenRouter (Optional Multi-Model)

**Goal:** Use your OpenRouter credits; optionally compare or fallback.

### Step 5.1 — OpenRouter call
- Add OpenRouter API call (e.g. with `httpx`). Use a model you have credits for (e.g. Gemini via OpenRouter or another model).
- Either: **replace** Gemini direct with OpenRouter, or **add** a second path (e.g. `?provider=openrouter`).

### Step 5.2 — Keep it simple
- Don’t build multi-model comparison yet. Just: "When I call OpenRouter, I get the same kind of summary/intent/risk."
- Same request/response shape as Phase 4.

**Checkpoint:** You can get explanations via OpenRouter using your free credits.

---

## Phase 6 — Frontend (Minimal)

**Goal:** A simple page where users paste a tx hash and see the explanation.

### Step 6.1 — One HTML page
- Single `index.html` (or a tiny React/Vue/Svelte app if you prefer).
- Input: text field for transaction hash.
- Button: "Explain".
- Call your backend `POST /explain` with the hash; show loading state.

### Step 6.2 — Show response
- Display: summary, intent, risk note, wallet changes, fee.
- No charts or fancy UI yet. Plain sections are fine.

### Step 6.3 — CORS
- Enable CORS in FastAPI so the frontend (different origin) can call the API.

**Checkpoint:** Paste hash in browser → see explanation from your API.

---

## Phase 7 — Deploy to DigitalOcean

**Goal:** API and (optional) frontend live on the internet.

### Step 7.1 — API deploy
- Push backend to GitHub.
- In DigitalOcean App Platform: New App → connect repo → select backend (Python, detect FastAPI).
- Set env vars: `GEMINI_API_KEY`, and OpenRouter key if used.
- Deploy; get public URL (e.g. `https://your-api.ondigitalocean.app`).

### Step 7.2 — Frontend (if separate)
- If frontend is static HTML/JS: same app or separate static site; set API URL to your DO API URL.
- If you use a simple SPA: build and deploy as static assets or small Node app.

### Step 7.3 — Test live
- Use a real tx hash against the live `/explain` endpoint. Confirm Gemini (and OpenRouter if used) work in production.

**Checkpoint:** Demo works end-to-end on DigitalOcean.

---

## Phase 8 — Nice-to-Haves (Only If Time)

Add **one at a time**, only if the core is solid:

- **Simple vs technical mode:** Two prompts or a single prompt with "explain for beginner" vs "include program names"; toggle in UI.
- **Voice (ElevenLabs):** One endpoint that takes your summary text and returns or streams audio. Optional button in UI.
- **Caching:** Store `tx_hash` → explanation in a small DB or file so repeat lookups are instant.
- **Helius (or similar):** Swap or supplement RPC with Helius for better token/instruction decoding, then pass that into Gemini.

---

## Summary Checklist

| Phase | What you have at the end |
|-------|---------------------------|
| 1     | API that fetches and parses a Solana tx |
| 2     | Gemini explains the tx in plain English |
| 3     | Wallet impact (SOL + tokens) in response |
| 4     | Intent + risk note in response |
| 5     | OpenRouter option using your credits |
| 6     | Minimal frontend: paste hash → see explanation |
| 7     | Deployed on DigitalOcean, demo-ready |
| 8     | Optional: simple/technical, voice, cache, better data |

---

## Tech Summary (No Overcomplication)

- **Backend:** Python, FastAPI, `httpx`, `google-generativeai`.
- **Data:** Solana public RPC (then Helius only if needed).
- **AI:** Gemini first; add OpenRouter when you’re ready.
- **Hosting:** DigitalOcean App Platform.
- **Frontend:** One page + fetch to your API.

Start at Phase 1 and move forward only when each checkpoint works.
