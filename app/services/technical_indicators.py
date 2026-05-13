from typing import Optional
import pandas as pd


def safe_float(value) -> Optional[float]:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def indicator_action(value: Optional[float], buy_above=None, sell_below=None) -> str:
    if value is None:
        return "—"

    if buy_above is not None and value >= buy_above:
        return "Compra"

    if sell_below is not None and value <= sell_below:
        return "Venda"

    return "Neutro"


def build_technical_indicators(df: pd.DataFrame) -> list[dict]:
    if df is None or df.empty:
        return []

    last = df.iloc[-1]

    rsi = safe_float(last.get("rsi14"))
    atr = safe_float(last.get("atr14"))
    close = safe_float(last.get("close"))

    indicators = [
        {
            "name": "RSI(14)",
            "value": round(rsi, 3) if rsi is not None else None,
            "action": indicator_action(rsi, buy_above=55, sell_below=45),
        },
        {
            "name": "ATR(14)",
            "value": round(atr, 6) if atr is not None else None,
            "action": "Mais Volatilidade" if atr and close and (atr / close) * 100 > 0.08 else "Neutro",
        },
    ]

    return indicators