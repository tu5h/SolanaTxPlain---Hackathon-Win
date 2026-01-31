"""Parse raw Solana transaction into a structured summary for AI."""

from typing import Any


def parse_tx(raw: dict) -> dict[str, Any]:
    """
    Extract fee, balance changes, and a short text summary from RPC result.
    Returns a dict suitable for the Gemini prompt.
    """
    meta = raw.get("meta") or {}
    tx = raw.get("transaction") or {}
    message = tx.get("message") or {}

    fee_lamports = meta.get("fee", 0)
    fee_sol = fee_lamports / 1_000_000_000

    account_keys = message.get("accountKeys") or []
    account_keys_list = (
        [a.get("pubkey") for a in account_keys if isinstance(a, dict)]
        if account_keys and isinstance(account_keys[0], dict)
        else list(account_keys) if account_keys else []
    )
    num_accounts = len(account_keys_list)

    instructions = message.get("instructions") or []
    num_instructions = len(instructions)

    pre_balances = meta.get("preBalances") or []
    post_balances = meta.get("postBalances") or []
    balance_changes = []
    for i, (pre, post) in enumerate(zip(pre_balances, post_balances)):
        delta = post - pre
        if delta != 0 and i < len(account_keys_list):
            acc = account_keys_list[i]
            balance_changes.append(
                {
                    "account_index": i,
                    "account": acc[:8] + "..." if isinstance(acc, str) else str(acc)[:8] + "...",
                    "before_sol": pre / 1_000_000_000,
                    "after_sol": post / 1_000_000_000,
                    "change_sol": delta / 1_000_000_000,
                }
            )

    pre_token = meta.get("preTokenBalances") or []
    post_token = meta.get("postTokenBalances") or []
    token_changes = []
    for pre in pre_token:
        post_entry = next(
            (p for p in post_token if p.get("accountIndex") == pre.get("accountIndex") and p.get("mint") == pre.get("mint")),
            None,
        )
        pre_ui = float((pre.get("uiTokenAmount") or {}).get("uiAmount") or 0)
        post_ui = float((post_entry.get("uiTokenAmount") or {}).get("uiAmount") or 0) if post_entry else 0
        mint = (pre.get("mint") or "unknown")[:8] + "..."
        if post_ui != pre_ui:
            token_changes.append({"mint": mint, "before": pre_ui, "after": post_ui, "change": post_ui - pre_ui})

    for post in post_token:
        if not any(p.get("accountIndex") == post.get("accountIndex") and p.get("mint") == post.get("mint") for p in pre_token):
            post_ui = float((post.get("uiTokenAmount") or {}).get("uiAmount") or 0)
            mint = (post.get("mint") or "unknown")[:8] + "..."
            token_changes.append({"mint": mint, "before": 0, "after": post_ui, "change": post_ui})

    log_messages = meta.get("logMessages") or []
    log_preview = "\n".join((log_messages or [])[:15])

    return {
        "fee_sol": round(fee_sol, 9),
        "fee_lamports": fee_lamports,
        "num_accounts": num_accounts,
        "num_instructions": num_instructions,
        "balance_changes": balance_changes,
        "token_changes": token_changes,
        "instruction_summary": _summarize_instructions(instructions),
        "log_preview": log_preview,
    }


def _summarize_instructions(instructions: list) -> str:
    """Brief summary of instruction program IDs."""
    parts = []
    for ix in instructions[:10]:
        program = ix.get("programId") or ix.get("program") or "unknown"
        if isinstance(program, str):
            parts.append(program[:12] + "...")
        else:
            parts.append(str(program)[:12] + "...")
    return ", ".join(parts) if parts else "none"
