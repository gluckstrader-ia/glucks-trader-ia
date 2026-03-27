import requests
import pandas as pd


BR_FUTURES_BRIDGE_URL = "http://127.0.0.1:9001"


def fetch_from_br_futures(symbol: str, timeframe: str = "5m", limit: int = 300) -> pd.DataFrame:
    response = requests.get(
        f"{BR_FUTURES_BRIDGE_URL}/candles",
        params={
            "symbol": symbol,
            "timeframe": timeframe,
            "limit": limit,
        },
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    required = ["datetime", "open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Resposta da ponte sem colunas obrigatórias: {missing}")

    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["datetime", "open", "high", "low", "close"])
    df = df.set_index("datetime").sort_index()

    return df[["open", "high", "low", "close", "volume"]]