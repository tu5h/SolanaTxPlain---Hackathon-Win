"""Fetch Solana transaction data via public RPC (README: Feature 1 — Transaction Fetching)."""

import httpx

SOLANA_RPC = "https://api.mainnet-beta.solana.com"


async def get_transaction(tx_hash: str) -> dict | None:
    """
    Fetch full transaction by signature.
    Returns RPC result: { meta, transaction } or None if not found.
    Data: instructions, accountKeys, logs, token balance changes, pre/post balances, fee.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            SOLANA_RPC,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [
                    tx_hash,
                    {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0},
                ],
            },
        )
        data = resp.json()
        if data.get("error"):
            return None
        return data.get("result")
