"""
AI layer (README: Features 3–4, 6–7).
- Intent detection (Feature 3)
- Plain English explanation (Feature 4)
- Risk signals (Feature 6)
- OpenRouter fallback (Feature 7)
"""

import logging
import os
from typing import Any

import google.generativeai as genai
import httpx

log = logging.getLogger("solana_tx_plain")

SECTION_LABELS = ("SUMMARY", "INTENT", "WALLET_IMPACT", "FEES", "PROGRAMS_USED", "RISK", "EXPLANATION")
SECTION_KEYS = {
    "SUMMARY": "summary",
    "INTENT": "intent",
    "WALLET_IMPACT": "wallet_impact",
    "FEES": "fees",
    "PROGRAMS_USED": "programs_used",
    "RISK": "risk",
    "EXPLANATION": "explanation",
}


def get_explanation(parsed: dict[str, Any], simple_mode: bool = True) -> dict[str, Any]:
    """
    Call Gemini with parsed tx. Returns:
      summary, intent, wallet_impact, fees, risk_flags, explanation, sections.
    On error: { "error": "...", "message": "..." }.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return _fallback("GEMINI_API_KEY not set.")
    genai.configure(api_key=api_key)
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    model = genai.GenerativeModel(model_name)
    prompt = _build_prompt(parsed, simple_mode)
    try:
        # Single prompt → generative content (text response)
        response = model.generate_content(prompt)
        if not response.candidates:
            try:
                reason = getattr(response.prompt_feedback, "block_reason", None) or "no content"
            except Exception:
                reason = "no content"
            return _fallback(f"Gemini blocked or empty: {reason}")
        # response.text is the standard way to get generated text from the SDK
        text = (response.text or "").strip()
        if not text:
            return _fallback("Gemini returned empty response.")
        out = _parse_response(text)
        risk_text = out.get("risk") or "No suspicious activity."
        out["risk_flags"] = [risk_text] if risk_text and risk_text.lower() not in ("none.", "no suspicious activity.", "—") else []
        return out
    except Exception as e:
        err_msg = str(e)
        is_429 = "429" in err_msg or "quota" in err_msg.lower() or "resource exhausted" in err_msg.lower() or "ResourceExhausted" in type(e).__name__
        if is_429:
            openrouter_key = os.environ.get("OPENROUTER_API_KEY") or ""
            openrouter_key = openrouter_key.strip() if isinstance(openrouter_key, str) else ""
            openrouter_result, openrouter_error = _try_openrouter(parsed, simple_mode)
            if openrouter_result and not openrouter_result.get("error"):
                return openrouter_result
            if openrouter_key:
                return {"error": "quota", "message": f"Gemini quota exceeded. OpenRouter fallback failed: {openrouter_error or 'unknown'}."}
            return {"error": "quota", "message": "Gemini quota exceeded. Put OPENROUTER_API_KEY in backend/.env and restart the server. Then check http://localhost:8000/debug to confirm it is loaded."}
        return {"error": "gemini", "message": err_msg[:300]}


def _try_openrouter(parsed: dict[str, Any], simple_mode: bool) -> tuple[dict[str, Any] | None, str | None]:
    """
    Try OpenRouter with same prompt. Returns (result_dict, error_message).
    If success: (result, None). If failure: (None, "reason").
    """
    api_key = (os.environ.get("OPENROUTER_API_KEY") or "").strip()
    if not api_key:
        log.info("OPENROUTER_API_KEY not set or empty — skipping fallback")
        return None, None
    prompt = _build_prompt(parsed, simple_mode)
    url = "https://openrouter.ai/api/v1/chat/completions"
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                url,
                json={
                    "model": os.environ.get("OPENROUTER_MODEL", "google/gemini-2.0-flash"),
                    "messages": [{"role": "user", "content": prompt}],
                },
                headers={"Authorization": f"Bearer {api_key}"},
            )
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        if resp.status_code != 200:
            err = body.get("error", {}).get("message") or body.get("message") or resp.text[:200] or f"HTTP {resp.status_code}"
            log.warning("OpenRouter HTTP %s: %s", resp.status_code, err)
            return None, f"HTTP {resp.status_code}: {err}"
        content = (body.get("choices") or [{}])[0].get("message", {}).get("content") or ""
        if not content.strip():
            return None, "Empty response from OpenRouter"
        out = _parse_response(content.strip())
        risk_text = out.get("risk") or "No suspicious activity."
        out["risk_flags"] = [risk_text] if risk_text and risk_text.lower() not in ("none.", "no suspicious activity.", "—") else []
        return out, None
    except Exception as e:
        log.warning("OpenRouter fallback failed: %s", e)
        return None, str(e)[:200]


def _fallback(msg: str) -> dict[str, Any]:
    return {
        "error": "config",
        "message": msg,
        "summary": "Explanation unavailable.",
        "intent": "unknown",
        "risk_flags": [],
        "explanation": msg,
    }


def _build_prompt(parsed: dict[str, Any], simple_mode: bool) -> str:
    mode = "Explain in simple terms for a beginner." if simple_mode else "Include program names and technical routing details."
    fee = parsed.get("fee_paid", 0)
    sol = parsed.get("sol_balance_change") or []
    tokens = parsed.get("token_balance_changes") or []
    programs = parsed.get("programs_used") or []
    instruction_types = parsed.get("instruction_types") or []
    log_preview = (parsed.get("log_preview") or "")[:1000]
    slot = parsed.get("slot")
    block_time = parsed.get("block_time")
    when = f"Slot: {slot}. Block time (Unix): {block_time}." if (slot is not None or block_time is not None) else ""

    return f"""You are a Solana transaction explainer. {mode}

From the transaction data below, reply with exactly these section headers and content (one line per header, content after the colon).

Required format:
SUMMARY: [1–2 sentences: what did this transaction do?]
INTENT: [One of: SOL transfer, token swap, NFT mint, liquidity add/remove, staking, contract interaction, token transfer, unknown]
WALLET_IMPACT: [What changed: SOL and/or token amounts, e.g. "SOL: -0.42. BONK: +132."]
FEES: [What was paid, e.g. "0.0005 SOL."]
PROGRAMS_USED: [Which app/program, e.g. "Jupiter Swap Router."]
RISK: [Anything risky or "No suspicious activity."]
EXPLANATION: [1–3 sentences: what happened in plain English.]

Transaction data:
- Fee (SOL): {fee}
- SOL balance changes: {sol}
- Token balance changes: {tokens}
- Programs: {programs[:10]}
- Instruction types: {instruction_types[:10]}
{f"- When: {when}" if when else ""}
- Log snippet:
{log_preview}

Reply with only the sectioned response."""


def _parse_response(text: str) -> dict[str, Any]:
    sections = {k: "" for k in SECTION_KEYS.values()}
    sections["summary"] = "No summary."
    sections["intent"] = "unknown"
    sections["risk"] = "No suspicious activity."
    sections["explanation"] = "—"

    current = None
    lines_acc = []

    def flush():
        nonlocal current, lines_acc
        if current and current in SECTION_KEYS:
            key = SECTION_KEYS[current]
            val = " ".join(lines_acc).strip()
            if val:
                sections[key] = val
        lines_acc = []

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            if current:
                lines_acc.append("")
            continue
        matched = False
        for label in SECTION_LABELS:
            if line.upper().startswith(label + ":"):
                flush()
                current = label
                rest = line[len(label) + 1:].strip()
                lines_acc = [rest] if rest else []
                matched = True
                break
        if not matched and current:
            lines_acc.append(line)
    flush()

    return {
        "sections": sections,
        "summary": sections.get("summary") or "No summary.",
        "intent": (sections.get("intent") or "unknown").strip().lower(),
        "wallet_impact": sections.get("wallet_impact") or "—",
        "fees": sections.get("fees") or "—",
        "programs_used": sections.get("programs_used") or "—",
        "risk": sections.get("risk") or "No suspicious activity.",
        "explanation": sections.get("explanation") or sections.get("summary") or "—",
        "risk_flags": [],
    }
