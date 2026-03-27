from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Literal
import pandas as pd

app = FastAPI(title="Profit Bridge", version="4.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
FEED_FILE = BASE_DIR / "profit_feed.csv"
HISTORY_FILE = BASE_DIR / "profit_history.csv"


def normalize_symbol(symbol: str) -> str:
    symbol = str(symbol).upper().strip().replace(" ", "")
    mapping = {
        "WINFUT": "WIN",
        "WDOFUT": "WDO",
        "WIN": "WIN",
        "WDO": "WDO",
    }
    return mapping.get(symbol, symbol)


def timeframe_to_rule(timeframe: str) -> str:
    mapping = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1h": "1h",
        "4h": "4h",
        "1d": "1D",
    }
    if timeframe not in mapping:
        raise ValueError(f"Timeframe inválido: {timeframe}")
    return mapping[timeframe]


def load_history() -> pd.DataFrame:
    if not HISTORY_FILE.exists():
        return pd.DataFrame(columns=["datetime", "symbol", "open", "high", "low", "close", "volume"])

    df = pd.read_csv(HISTORY_FILE)

    required = ["datetime", "symbol", "open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"profit_history.csv sem colunas obrigatórias: {missing}")

    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df["symbol"] = df["symbol"].astype(str).apply(normalize_symbol)

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["datetime", "symbol", "open", "high", "low", "close"])
    return df


def load_current_feed() -> pd.DataFrame:
    if not FEED_FILE.exists():
        return pd.DataFrame(columns=["datetime", "symbol", "open", "high", "low", "close", "volume"])

    df = pd.read_csv(FEED_FILE)

    required = ["datetime", "symbol", "open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return pd.DataFrame(columns=["datetime", "symbol", "open", "high", "low", "close", "volume"])

    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df["symbol"] = df["symbol"].astype(str).apply(normalize_symbol)

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["datetime", "symbol", "open", "high", "low", "close"])
    return df


def resample_ohlcv(df: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    symbol = normalize_symbol(symbol)
    df = df[df["symbol"] == symbol].copy()
    if df.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    df = df.set_index("datetime").sort_index()
    rule = timeframe_to_rule(timeframe)

    candles = df.resample(rule).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    })

    candles = candles.dropna(subset=["open", "high", "low", "close"])
    return candles


@app.get("/health")
def health():
    return {
        "status": "ok",
        "feed_file": str(FEED_FILE),
        "history_file": str(HISTORY_FILE)
    }


@app.get("/symbols")
def symbols():
    hist = load_history()
    feed = load_current_feed()

    all_symbols = set()
    if not hist.empty:
        all_symbols.update(hist["symbol"].unique().tolist())
    if not feed.empty:
        all_symbols.update(feed["symbol"].unique().tolist())

    return {"symbols": sorted(all_symbols)}


@app.get("/candles")
def candles(
    symbol: str = Query(...),
    timeframe: Literal["1m", "5m", "15m", "30m", "1h", "4h", "1d"] = Query("5m"),
    limit: int = Query(300, ge=10, le=5000),
):
    try:
        hist = load_history()
        feed = load_current_feed()

        hist_candles = resample_ohlcv(hist, symbol, timeframe)
        feed_candles = resample_ohlcv(feed, symbol, timeframe)

        combined = pd.concat([hist_candles, feed_candles])
        combined = combined[~combined.index.duplicated(keep="last")]
        combined = combined.sort_index().tail(limit)

        if combined.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Sem candles para {symbol} no timeframe {timeframe}"
            )

        result = []
        for idx, row in combined.iterrows():
            result.append({
                "datetime": idx.isoformat(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            })

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))