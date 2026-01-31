"""Generate plain-English explanation and intent using Gemini."""

import os
from typing import Any

import google.generativeai as genai


def get_explanation(parsed: dict[str, Any]) -> dict[str, str]:
    """
    Call Gemini with parsed tx data. Returns summary, intent, risk_note.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {
            "summary": "AI explanation unavailable: GEMINI_API_KEY not set.",
            "intent": "unknown",
            "risk_note": "Cannot assess risk without API key.",
        }

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = _build_prompt(parsed)
    try:
        response = model.generate_content(prompt)
        text = (response.text or "").strip()
    except Exception as e:
        return {
            "summary": f"AI explanation failed: {e!s}",
            "intent": "unknown",
            "risk_note": "Error during analysis.",
        }

    return _parse_ai_response(text, parsed)


def _build_prompt(parsed: dict[str, Any]) -> str:
    fee = parsed.get("fee_sol", 0)
    balance_changes = parsed.get("balance_changes") or []
    token_changes = parsed.get("token_changes") or []
    instruction_summary = parsed.get("instruction_summary", "")
    log_preview = (parsed.get("log_preview") or "")[:800]

    return f"""You are a Solana transaction explainer. Based ONLY on this transaction data, reply in this exact format (each line starting with the label):

SUMMARY: [1-2 sentences in plain English: what did this transaction do?]
INTENT: [exactly one of: SOL transfer, token swap, NFT mint, staking, liquidity add/remove, contract interaction, token transfer, other]
RISK: [One short sentence: anything risky or unusual? Or "Nothing obvious."]

Transaction data:
- Fee: {fee} SOL
- Balance changes (SOL): {balance_changes}
- Token balance changes: {token_changes}
- Programs/instructions: {instruction_summary}
- Log snippet:
{log_preview}
"""


def _parse_ai_response(text: str, parsed: dict[str, Any]) -> dict[str, str]:
    summary = "No summary generated."
    intent = "unknown"
    risk_note = "Nothing obvious."

    for line in text.split("\n"):
        line = line.strip()
        if line.upper().startswith("SUMMARY:"):
            summary = line.split(":", 1)[-1].strip()
        elif line.upper().startswith("INTENT:"):
            intent = line.split(":", 1)[-1].strip().lower()
        elif line.upper().startswith("RISK:"):
            risk_note = line.split(":", 1)[-1].strip()

    return {
        "summary": summary or "No summary generated.",
        "intent": intent or "unknown",
        "risk_note": risk_note or "Nothing obvious.",
    }
