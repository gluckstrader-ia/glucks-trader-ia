import requests
import pandas as pd

from app.core.config import TWELVE_DATA_API_KEY


def fetch_from_twelve_data(
    symbol: str,
    interval: str = "5min",
    outputsize: int = 200
) -> pd.DataFrame:
    if not TWELVE_DATA_API_KEY:
        raise ValueError("TWELVE_DATA_API_KEY não configurada")

    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": TWELVE_DATA_API_KEY,
        "format": "JSON",
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()

    if "values" not in data:
        raise ValueError(f"Resposta inválida Twelve Data: {data}")

    df = pd.DataFrame(data["values"])

    if df.empty:
        raise ValueError("Twelve Data retornou DataFrame vazio")

    if "volume" not in df.columns:
        df["volume"] = 0

    numeric_cols = ["open", "high", "low", "close", "volume"]

    for col in numeric_cols:
        if col not in df.columns:
            if col == "volume":
                df[col] = 0
            else:
                raise ValueError(f"Coluna ausente no Twelve Data: {col}")

        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["datetime", "open", "high", "low", "close"])
    df = df.sort_values("datetime").set_index("datetime")

    return df[["open", "high", "low", "close", "volume"]]