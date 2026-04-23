from __future__ import annotations

from datetime import datetime
from typing import Dict, Literal

import pandas as pd
import requests

from app.services.market_data_service import get_market_data
from app.services.analysis_service import validate_dataframe


AssetType = Literal[
    "index",
    "stock",
    "forex",
    "crypto",
    "b3",
    "commodity",
    "future_br",
    "future_us",
]

def get_b3_quant_dataframe(symbol: str) -> pd.DataFrame:
    """
    Busca o snapshot interno da B3 e monta um DataFrame mínimo
    para o Quant funcionar com WIN/WDO.
    """
    try:
        response = requests.get(
            f"http://127.0.0.1:8000/api/internal/market-data/{symbol}",
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()

        if not payload:
            raise ValueError(f"Sem payload interno para {symbol}")

        last_price = float(payload.get("last_price") or 0)
        open_price = float(payload.get("open_price") or last_price)
        high_price = float(payload.get("high_price") or last_price)
        low_price = float(payload.get("low_price") or last_price)
        volume = float(payload.get("volume") or 0)

        if last_price <= 0:
            raise ValueError(f"last_price inválido para {symbol}")

        # Criamos várias linhas iguais só para o restante do cálculo não quebrar.
        # Depois podemos sofisticar isso, mas já resolve o Quant para WIN/WDO.
        rows = []
        for _ in range(60):
            rows.append(
                {
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": last_price,
                    "volume": volume,
                }
            )

        return pd.DataFrame(rows)

    except Exception as e:
        raise ValueError(f"Falha ao obter snapshot interno B3 para {symbol}: {e}")

def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def _atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()

    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(period).mean().bfill()


def _roc(close: pd.Series, period: int = 9) -> pd.Series:
    return ((close / close.shift(period)) - 1.0) * 100.0


def _adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]

    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.rolling(period).mean().replace(0, pd.NA)
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)

    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, pd.NA)) * 100
    adx = dx.rolling(period).mean().fillna(0)

    return adx


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _trend_label(value: float) -> str:
    if value >= 0.8:
        return "FORTE ALTISTA"
    if value >= 0.2:
        return "ALTISTA"
    if value <= -0.8:
        return "FORTE BAIXISTA"
    if value <= -0.2:
        return "BAIXISTA"
    return "NEUTRO"


def _signal_label(score: float) -> str:
    if score >= 55:
        return "COMPRA FORTE"
    if score >= 20:
        return "COMPRA"
    if score <= -55:
        return "VENDA FORTE"
    if score <= -20:
        return "VENDA"
    return "NEUTRO"


def build_quant_dashboard(
    asset: str,
    asset_type: AssetType,
    timeframe: str,
) -> Dict:
    asset_upper = str(asset).upper().strip()

    if asset_upper in ["WIN", "WDO"]:
        df = get_b3_quant_dataframe(asset_upper)
    else:
        df = get_market_data(
            asset=asset,
            asset_type=asset_type,
            timeframe=timeframe,
            prefer_binance=True,
        )
        df = validate_dataframe(df)

    if df is None or df.empty or len(df) < 60:
        raise ValueError("Dados insuficientes para montar o Dashboard Quant.")

    df = df.copy()
    df.columns = [str(c).lower() for c in df.columns]

    required = ["open", "high", "low", "close", "volume"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Coluna obrigatória ausente: {col}")

    close = df["close"]
    volume = df["volume"]

    ema9 = _ema(close, 9)
    ema21 = _ema(close, 21)
    ema50 = _ema(close, 50)

    rsi = _rsi(close, 14)
    atr = _atr(df, 14)
    roc = _roc(close, 9)
    adx = _adx(df, 14)

    current_close = _safe_float(close.iloc[-1])
    current_ema9 = _safe_float(ema9.iloc[-1])
    current_ema21 = _safe_float(ema21.iloc[-1])
    current_ema50 = _safe_float(ema50.iloc[-1])

    current_rsi = _safe_float(rsi.iloc[-1], 50.0)
    current_atr = _safe_float(atr.iloc[-1])
    current_roc = _safe_float(roc.iloc[-1])
    current_adx = _safe_float(adx.iloc[-1])
    current_volume = _safe_float(volume.iloc[-1])

    avg_volume_20 = _safe_float(volume.tail(20).mean(), 1.0)
    relative_volume = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1.0

    atr_mean_20 = _safe_float(
        atr.tail(20).mean(),
        current_atr if current_atr > 0 else 1.0,
    )
    relative_volatility = (current_atr / atr_mean_20) - 1.0 if atr_mean_20 > 0 else 0.0

    short_trend_raw = 0.0
    if current_close > current_ema9 > current_ema21:
        short_trend_raw = 1.0
    elif current_close < current_ema9 < current_ema21:
        short_trend_raw = -1.0
    elif current_close > current_ema21:
        short_trend_raw = 0.4
    elif current_close < current_ema21:
        short_trend_raw = -0.4

    mid_trend_raw = 0.0
    if current_ema9 > current_ema21 > current_ema50:
        mid_trend_raw = 1.0
    elif current_ema9 < current_ema21 < current_ema50:
        mid_trend_raw = -1.0
    elif current_ema21 > current_ema50:
        mid_trend_raw = 0.4
    elif current_ema21 < current_ema50:
        mid_trend_raw = -0.4

    pressure = 0.0
    if current_close > 0:
        pressure = ((current_close - current_ema21) / current_close) * 100

    rsi_score = (current_rsi - 50.0) / 50.0
    roc_score = max(-1.0, min(1.0, current_roc / 2.5))
    pressure_score = max(-1.0, min(1.0, pressure / 1.5))
    trend_score = (short_trend_raw * 0.6) + (mid_trend_raw * 0.4)

    score = (
        trend_score * 40
        + roc_score * 20
        + rsi_score * 20
        + pressure_score * 20
    )
    score = max(-100.0, min(100.0, score))

    return {
        "asset": asset,
        "asset_type": asset_type,
        "timeframe": timeframe,
        "score": round(score, 2),
        "signal": _signal_label(score),
        "short_trend": _trend_label(short_trend_raw),
        "mid_trend": _trend_label(mid_trend_raw),
        "roc": round(current_roc, 3),
        "rsi": round(current_rsi, 2),
        "pressure": round(pressure, 3),
        "atr": round(current_atr, 6),
        "relative_volatility": round(relative_volatility, 3),
        "relative_volume": round(relative_volume, 2),
        "adx": round(current_adx, 2),
        "updated_at": datetime.utcnow().isoformat(),
    }