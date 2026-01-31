"""Fetch and parse Solana transaction data via public RPC."""

import httpx

SOLANA_RPC = "https://api.mainnet-beta.solana.com"


async def get_transaction(tx_hash: str) -> dict | None:
    """Fetch transaction by signature. Returns raw RPC response or None."""
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
        if "error" in data:
            return None
        return data.get("result")
