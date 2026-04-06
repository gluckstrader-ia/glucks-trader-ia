import pandas as pd

from .types import DowData


def _trend_label(start_price: float, end_price: float, neutral_band: float = 0.002) -> str:
    if start_price <= 0:
        return "LATERAL"

    change = (end_price - start_price) / start_price

    if change > neutral_band:
        return "ALTA"
    if change < -neutral_band:
        return "BAIXA"
    return "LATERAL"


def _market_phase(primary: str, secondary: str, minor: str) -> tuple[str, float]:
    if primary == "ALTA" and secondary == "ALTA":
        return "ACUMULAÇÃO", 68.0
    if primary == "ALTA" and secondary == "LATERAL":
        return "EXPANSÃO", 60.0
    if primary == "BAIXA" and secondary == "BAIXA":
        return "DISTRIBUIÇÃO", 72.0
    if primary == "BAIXA" and secondary == "LATERAL":
        return "MARKDOWN", 62.0
    return "LATERALIZAÇÃO", 35.0


def calculate_dow(df: pd.DataFrame) -> DowData:
    close = df["close"]

    primary = _trend_label(float(close.tail(80).iloc[0]), float(close.tail(80).iloc[-1])) if len(close) >= 80 else "LATERAL"
    secondary = _trend_label(float(close.tail(30).iloc[0]), float(close.tail(30).iloc[-1])) if len(close) >= 30 else "LATERAL"
    minor = _trend_label(float(close.tail(10).iloc[0]), float(close.tail(10).iloc[-1])) if len(close) >= 10 else "LATERAL"

    phase, phase_score = _market_phase(primary, secondary, minor)

    vol = df["volume"].tail(20)
    vol_mean = float(vol.mean()) if len(vol) > 0 else 0.0
    vol_last = float(vol.iloc[-1]) if len(vol) > 0 else 0.0

    price_volume_confirmation = "CONFIRMADO" if vol_mean > 0 and vol_last >= vol_mean else "NÃO CONFIRMADO"
    indices_confirmation = "CONFIRMADO" if primary == secondary else "NÃO CONFIRMADO"
    volume_note = (
        "Volume confirma o movimento dominante."
        if price_volume_confirmation == "CONFIRMADO"
        else "Volume não confirma - possível reversão"
    )

    return DowData(
        primary=primary,
        secondary=secondary,
        minor=minor,
        market_phase=phase,
        market_phase_score=round(phase_score, 1),
        price_volume_confirmation=price_volume_confirmation,
        indices_confirmation=indices_confirmation,
        volume_note=volume_note,
    )