from time import time
from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/internal/market-data", tags=["market-data"])

MARKET_CACHE: Dict[str, Dict[str, Any]] = {
    "WIN": {},
    "WDO": {},
}

LAST_UPDATE_TS = 0.0


class MarketIngestPayload(BaseModel):
    assets: Dict[str, Dict[str, Any]]


@router.post("")
def ingest_market_data(
    payload: MarketIngestPayload,
    x_ingest_token: str | None = Header(default=None),
):
    import os

    expected = os.getenv("GLUCKS_INGEST_TOKEN", "").strip()
    if not expected or x_ingest_token != expected:
        raise HTTPException(status_code=401, detail="Token de ingestão inválido")

    global LAST_UPDATE_TS

    for symbol, data in payload.assets.items():
        MARKET_CACHE[symbol.upper()] = data

    LAST_UPDATE_TS = time()
    return {"ok": True, "updated_at": LAST_UPDATE_TS}


@router.get("/{symbol}")
def get_market_data(symbol: str):
    symbol = symbol.strip().upper()

    if symbol not in MARKET_CACHE or not MARKET_CACHE[symbol]:
        raise HTTPException(status_code=404, detail="Ativo sem dados em memória")

    return {
        "ok": True,
        "symbol": symbol,
        "data": MARKET_CACHE[symbol],
        "updated_at": LAST_UPDATE_TS,
    }