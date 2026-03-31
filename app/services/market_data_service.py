import pandas as pd
import yfinance as yf

from app.services.symbol_resolver import (
    get_twelve_data_symbol,
    get_yfinance_symbol,
    get_br_futures_symbol,
)
from app.services.twelvedata_service import fetch_from_twelve_data
from app.services.binance_service import fetch_from_binance
from app.services.br_futures_service import fetch_from_br_futures


def normalize_yfinance_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            "_".join([str(c).strip().lower() for c in col if str(c).strip()])
            for col in df.columns
        ]
    else:
        df.columns = [str(col).strip().lower() for col in df.columns]

    rename_map = {}

    for col in df.columns:
        c = col.lower()

        if "open" in c:
            rename_map[col] = "open"
        elif "high" in c:
            rename_map[col] = "high"
        elif "low" in c:
            rename_map[col] = "low"
        elif "close" in c and "adj" not in c:
            rename_map[col] = "close"
        elif "volume" in c:
            rename_map[col] = "volume"

    df = df.rename(columns=rename_map)

    wanted = ["open", "high", "low", "close", "volume"]
    existing = [c for c in wanted if c in df.columns]
    df = df[existing].copy()

    if "volume" not in df.columns:
        df["volume"] = 0

    for col in wanted:
        if col not in df.columns:
            df[col] = 0

    df = df[wanted]

    for col in wanted:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["open", "high", "low", "close"])
    return df


def timeframe_to_yfinance_interval(timeframe: str) -> str:
    mapping = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "60m",
        "4h": "60m",
        "1d": "1d",
    }
    return mapping.get(timeframe, "5m")


def timeframe_to_twelvedata_interval(timeframe: str) -> str:
    mapping = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1h": "1h",
        "4h": "4h",
        "1d": "1day",
    }
    return mapping.get(timeframe, "5min")


def period_for_asset(asset_type: str, timeframe: str) -> str:
    if timeframe == "1m":
        return "7d"
    if timeframe in {"5m", "15m", "30m"}:
        return "30d"
    if timeframe in {"1h", "4h"}:
        return "90d"
    return "1y"


def fetch_from_yfinance(symbol: str, timeframe: str, asset_type: str) -> pd.DataFrame:
    period = period_for_asset(asset_type, timeframe)
    interval = timeframe_to_yfinance_interval(timeframe)

    df = yf.download(
        symbol,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        threads=False,
    )

    return normalize_yfinance_columns(df)


def is_pre_resolved_yfinance_symbol(asset: str) -> bool:
    asset = str(asset).upper().strip()

    # exemplos:
    # GC=F, MGC=F, NQ=F, EURUSD=X, BTC-USD, PETR4.SA, ^BVSP
    return (
        "=F" in asset
        or "=X" in asset
        or asset.endswith(".SA")
        or asset.startswith("^")
        or "-USD" in asset
    )


def get_market_data(
    asset: str,
    asset_type: str,
    timeframe: str,
    prefer_binance: bool = True,
) -> pd.DataFrame:
    asset = str(asset).upper().strip()
    asset_type = str(asset_type).lower().strip()

    if asset_type == "forex":
        # Se já veio resolvido para yfinance (ex: GC=F), pula TwelveData
        if is_pre_resolved_yfinance_symbol(asset):
            try:
                df = fetch_from_yfinance(asset, timeframe, asset_type)
                if not df.empty:
                    return df
            except Exception as e:
                print(f"[FALLBACK] yfinance falhou para forex resolvido {asset}: {e}")
        else:
            try:
                td_symbol = get_twelve_data_symbol(asset)
                df = fetch_from_twelve_data(
                    symbol=td_symbol,
                    interval=timeframe_to_twelvedata_interval(timeframe),
                    outputsize=300,
                )
                if not df.empty:
                    return df
            except Exception as e:
                print(f"[FALLBACK] Twelve Data falhou para {asset}: {e}")

            try:
                yf_symbol = get_yfinance_symbol(asset, asset_type)
                df = fetch_from_yfinance(yf_symbol, timeframe, asset_type)
                if not df.empty:
                    return df
            except Exception as e:
                print(f"[FALLBACK] yfinance falhou para forex {asset}: {e}")

    elif asset_type == "crypto":
        if prefer_binance and not is_pre_resolved_yfinance_symbol(asset):
            try:
                df = fetch_from_binance(symbol=asset, timeframe=timeframe, limit=300)
                if not df.empty:
                    return df
            except Exception as e:
                print(f"[FALLBACK] Binance falhou para {asset}: {e}")

        try:
            yf_symbol = asset if is_pre_resolved_yfinance_symbol(asset) else get_yfinance_symbol(asset, asset_type)
            df = fetch_from_yfinance(yf_symbol, timeframe, asset_type)
            if not df.empty:
                return df
        except Exception as e:
            print(f"[FALLBACK] yfinance falhou para crypto {asset}: {e}")

    elif asset_type == "future_br":
        try:
            br_symbol = get_br_futures_symbol(asset)
            df = fetch_from_br_futures(
                symbol=br_symbol,
                timeframe=timeframe,
                limit=300,
            )
            if not df.empty:
                return df
        except Exception as e:
            print(f"[FALLBACK] futuros BR falhou para {asset}: {e}")

        raise ValueError(f"Provider de futuros BR não configurado ou sem dados para {asset}")

    elif asset_type in {"future_us", "futuro_us", "futuros_us"}:
        try:
            yf_symbol = asset if is_pre_resolved_yfinance_symbol(asset) else get_yfinance_symbol(asset, asset_type)
            df = fetch_from_yfinance(yf_symbol, timeframe, asset_type)
            if not df.empty:
                return df
        except Exception as e:
            print(f"[FALLBACK] yfinance falhou para futuros US {asset}: {e}")

    elif asset_type in {
        "stock",
        "acao",
        "acoes",
        "index",
        "indices",
        "b3",
        "acao_br",
        "acoes_br",
        "stock_br",
    }:
        try:
            yf_symbol = asset if is_pre_resolved_yfinance_symbol(asset) else get_yfinance_symbol(asset, asset_type)
            df = fetch_from_yfinance(yf_symbol, timeframe, asset_type)
            if not df.empty:
                return df
        except Exception as e:
            print(f"[FALLBACK] yfinance falhou para {asset_type} {asset}: {e}")

    else:
        try:
            yf_symbol = asset if is_pre_resolved_yfinance_symbol(asset) else get_yfinance_symbol(asset, asset_type)
            df = fetch_from_yfinance(yf_symbol, timeframe, asset_type)
            if not df.empty:
                return df
        except Exception as e:
            print(f"[FALLBACK] yfinance falhou para {asset}: {e}")

    raise ValueError(f"Não foi possível obter dados para {asset} ({asset_type}) no timeframe {timeframe}")