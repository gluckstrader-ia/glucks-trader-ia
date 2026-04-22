from datetime import datetime
from typing import Dict


SUPPORTED_LIVE_ASSETS = {
    "WIN": {"display_name": "Mini Índice", "market": "future_br"},
    "WDO": {"display_name": "Mini Dólar", "market": "future_br"},
    "EURUSD": {"display_name": "Euro/Dólar", "market": "forex"},
    "XAUUSD": {"display_name": "Ouro", "market": "forex"},
    "BTCUSD": {"display_name": "Bitcoin", "market": "crypto"},
    "NASDAQ": {"display_name": "Nasdaq", "market": "index"},
    "SPX": {"display_name": "S&P 500", "market": "index"},
}


def normalize_live_asset(asset: str) -> str:
    return asset.strip().upper()


def validate_live_asset(asset: str) -> str:
    normalized = normalize_live_asset(asset)
    if normalized not in SUPPORTED_LIVE_ASSETS:
        supported = ", ".join(SUPPORTED_LIVE_ASSETS.keys())
        raise ValueError(
            f"Ativo '{asset}' não suportado na Sala ao Vivo IA. "
            f"Ativos suportados: {supported}"
        )
    return normalized


def get_initial_market_state(asset: str, timeframe: str = "5m") -> Dict:
    normalized = validate_live_asset(asset)

    return {
        "asset": normalized,
        "timeframe": timeframe,
        "price": 0.0,
        "market_regime": "neutral",
        "updated_at": datetime.utcnow(),
        "metadata": SUPPORTED_LIVE_ASSETS[normalized],
    }