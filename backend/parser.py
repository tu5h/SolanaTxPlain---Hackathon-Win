"""
Transaction Parser (README: Feature 2).
Converts raw RPC response into structured data for AI and API.
Output: sol_balance_change, token_balance_changes, programs_used, fee_paid, instruction_types.
"""

from typing import Any


def parse_tx(raw: dict) -> dict[str, Any]:
    """
    raw = RPC getTransaction result: { meta, transaction }.
    Returns structured summary per README:
      sol_balance_change, token_balance_changes, programs_used, fee_paid, instruction_types
    """
    meta = raw.get("meta") or {}
    tx = raw.get("transaction") or {}
    message = tx.get("message") or {}

    fee_lamports = meta.get("fee", 0)
    fee_paid = fee_lamports / 1_000_000_000

    account_keys = message.get("accountKeys") or []
    account_keys_list = (
        [a.get("pubkey") for a in account_keys if isinstance(a, dict)]
        if account_keys and isinstance(account_keys[0], dict)
        else list(account_keys) if account_keys else []
    )

    pre_balances = meta.get("preBalances") or []
    post_balances = meta.get("postBalances") or []
    sol_balance_change = []
    for i, (pre, post) in enumerate(zip(pre_balances, post_balances)):
        delta = post - pre
        if delta != 0 and i < len(account_keys_list):
            acc = account_keys_list[i]
            pubkey = acc if isinstance(acc, str) else str(acc)
            sol_balance_change.append({
                "account": pubkey[:12] + "..." if len(pubkey) > 12 else pubkey,
                "before_sol": round(pre / 1_000_000_000, 9),
                "after_sol": round(post / 1_000_000_000, 9),
                "change_sol": round(delta / 1_000_000_000, 9),
            })

    pre_token = meta.get("preTokenBalances") or []
    post_token = meta.get("postTokenBalances") or []
    token_balance_changes = []
    for pre in pre_token:
        post_entry = next(
            (p for p in post_token if p.get("accountIndex") == pre.get("accountIndex") and p.get("mint") == pre.get("mint")),
            None,
        )
        pre_ui = float((pre.get("uiTokenAmount") or {}).get("uiAmount") or 0)
        post_ui = float((post_entry.get("uiTokenAmount") or {}).get("uiAmount") or 0) if post_entry else 0
        mint = (pre.get("mint") or "unknown")[:12] + "..."
        if post_ui != pre_ui:
            token_balance_changes.append({
                "mint": mint,
                "before": pre_ui,
                "after": post_ui,
                "change": round(post_ui - pre_ui, 6),
            })
    for post in post_token:
        if not any(p.get("accountIndex") == post.get("accountIndex") and p.get("mint") == post.get("mint") for p in pre_token):
            post_ui = float((post.get("uiTokenAmount") or {}).get("uiAmount") or 0)
            mint = (post.get("mint") or "unknown")[:12] + "..."
            token_balance_changes.append({"mint": mint, "before": 0, "after": post_ui, "change": round(post_ui, 6)})

    instructions = message.get("instructions") or []
    program_ids = []
    instruction_types = []
    for ix in instructions[:20]:
        pid = ix.get("programId") or ix.get("program") or "unknown"
        program_ids.append(pid if isinstance(pid, str) else str(pid))
        instruction_types.append(_instruction_type(ix))

    programs_used = list(dict.fromkeys(program_ids))  # unique order-preserving
    log_messages = meta.get("logMessages") or []
    log_preview = "\n".join(log_messages[:20])

    return {
        "sol_balance_change": sol_balance_change,
        "token_balance_changes": token_balance_changes,
        "programs_used": programs_used,
        "fee_paid": round(fee_paid, 9),
        "fee_lamports": fee_lamports,
        "instruction_types": instruction_types,
        "num_instructions": len(instructions),
        "log_preview": log_preview,
    }


def _instruction_type(ix: dict) -> str:
    """Brief label for instruction (program name or 'unknown')."""
    pid = ix.get("programId") or ix.get("program") or ""
    s = pid if isinstance(pid, str) else str(pid)
    if "11111111111111111111" in s:
        return "system"
    if "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA" in s or "Token" in s:
        return "spl-token"
    return s[:16] + "..." if len(s) > 16 else s or "unknown"
