from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_current_active_user
from app.models import User

# IMPORTANTE:
# ajuste o caminho abaixo para o arquivo onde estão MARKET_CACHE e LAST_UPDATE_TS
from app.api.market_data import MARKET_CACHE, LAST_UPDATE_TS

router = APIRouter(tags=["market-live"])


@router.get("/market/live")
def get_live_market(
    symbol: str = Query(..., description="Símbolo, ex: WIN ou WDO"),
    asset_type: str = Query(..., description="Tipo do ativo, ex: future_br"),
    current_user: User = Depends(get_current_active_user),
):
    normalized_symbol = (symbol or "").strip().upper()
    normalized_asset_type = (asset_type or "").strip().lower()

    if normalized_asset_type != "future_br":
        raise HTTPException(
            status_code=400,
            detail="Este endpoint é exclusivo para future_br.",
        )

    if normalized_symbol not in {"WIN", "WDO"}:
        raise HTTPException(
            status_code=400,
            detail="Este endpoint é exclusivo para WIN e WDO.",
        )

    if normalized_symbol not in MARKET_CACHE or not MARKET_CACHE[normalized_symbol]:
        raise HTTPException(
            status_code=404,
            detail=f"{normalized_symbol} sem dados em memória.",
        )

    raw: Dict[str, Any] = MARKET_CACHE[normalized_symbol]

    return {
        "symbol": normalized_symbol,
        "asset_type": normalized_asset_type,
        "last_price": raw.get("last_price"),
        "bid": raw.get("bid"),
        "ask": raw.get("ask"),
        "last_trade_ts": raw.get("last_trade_ts"),
        "updated_at": LAST_UPDATE_TS,
        "source": raw.get("source", "b3_nelogica"),
    }