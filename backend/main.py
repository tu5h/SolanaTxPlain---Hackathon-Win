"""
SolanaTxPlain API — fetch Solana tx, parse, explain with Gemini.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ai_explain import get_explanation
from parser import parse_tx
from solana_client import get_transaction

app = FastAPI(
    title="SolanaTxPlain",
    description="AI-powered Solana transaction explainer",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExplainRequest(BaseModel):
    tx_hash: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/explain")
async def explain(req: ExplainRequest):
    tx_hash = (req.tx_hash or "").strip()
    if not tx_hash:
        raise HTTPException(status_code=400, detail="tx_hash is required")

    raw = await get_transaction(tx_hash)
    if not raw:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found. Check the hash and try again.",
        )

    parsed = parse_tx(raw)
    ai = get_explanation(parsed)

    return {
        "summary": ai["summary"],
        "intent": ai["intent"],
        "risk_note": ai["risk_note"],
        "wallet_changes": {
            "fee_sol": parsed.get("fee_sol"),
            "balance_changes": parsed.get("balance_changes"),
            "token_changes": parsed.get("token_changes"),
        },
        "explanation": ai["summary"],
    }


# Serve frontend
_frontend = Path(__file__).resolve().parent.parent / "frontend"
_index = _frontend / "index.html"


@app.get("/")
def index():
    if _index.exists():
        return FileResponse(_index)
    return {"message": "SolanaTxPlain API", "docs": "/docs", "health": "/health"}


@app.get("/favicon.ico")
def favicon():
    return FileResponse(_frontend / "favicon.ico") if (_frontend / "favicon.ico").exists() else None
