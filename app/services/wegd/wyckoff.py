from typing import Dict, List

import pandas as pd

from .types import WyckoffData, WyckoffEvent


def _classify_phase(close_now: float, sma20: float, sma50: float, rsi: float) -> str:
    if close_now > sma20 > sma50 and rsi >= 55:
        return "Markup"
    if close_now < sma20 < sma50 and rsi <= 45:
        return "Markdown"
    if sma20 > sma50 and 45 <= rsi <= 55:
        return "Acumulação"
    if sma20 < sma50 and 45 <= rsi <= 55:
        return "Distribuição"
    return "Indefinido"


def _next_phase(phase: str) -> str:
    mapping = {
        "Acumulação": "Markup",
        "Markup": "Distribuição",
        "Distribuição": "Markdown",
        "Markdown": "Acumulação",
        "Indefinido": "Indefinido",
    }
    return mapping.get(phase, "Indefinido")


def _composite_man(phase: str) -> str:
    if phase in {"Acumulação", "Markup"}:
        return "Comprador"
    if phase in {"Distribuição", "Markdown"}:
        return "Vendedor"
    return "Neutro"


def _volume_state(df: pd.DataFrame) -> Dict[str, str]:
    vol = df["volume"].tail(20)
    if len(vol) < 5:
        return {"volume_state": "Normal", "volume_label": "Médio"}

    mean_vol = float(vol.mean())
    last_vol = float(vol.iloc[-1])

    if mean_vol <= 0:
        return {"volume_state": "Normal", "volume_label": "Médio"}

    ratio = last_vol / mean_vol

    if ratio >= 1.35:
        return {"volume_state": "Expansão", "volume_label": "Alto"}
    if ratio <= 0.75:
        return {"volume_state": "Contração", "volume_label": "Baixo"}
    return {"volume_state": "Normal", "volume_label": "Médio"}


def calculate_wyckoff(
    df: pd.DataFrame,
    close_now: float,
    sma20: float,
    sma50: float,
    rsi: float,
) -> WyckoffData:
    phase = _classify_phase(close_now, sma20, sma50, rsi)

    confidence = 50.0
    if phase == "Markup":
        confidence = 72.0
    elif phase == "Markdown":
        confidence = 72.0
    elif phase in {"Acumulação", "Distribuição"}:
        confidence = 60.0

    progress = confidence
    next_phase = _next_phase(phase)
    composite = _composite_man(phase)

    events_confirmed: List[WyckoffEvent] = []
    events_pending: List[WyckoffEvent] = []

    last_high = float(df["high"].tail(20).max())
    last_low = float(df["low"].tail(20).min())

    if phase == "Markup":
        events_confirmed.append(
            WyckoffEvent(
                name="SOS",
                desc="Sinal de força com continuidade compradora",
                price=last_high,
            )
        )
        events_pending.append(
            WyckoffEvent(
                name="LPS",
                desc="Pullback ideal para continuação da tendência",
                price=close_now,
            )
        )
    elif phase == "Markdown":
        events_confirmed.append(
            WyckoffEvent(
                name="SOW",
                desc="Sinal de fraqueza com continuidade vendedora",
                price=last_low,
            )
        )
        events_pending.append(
            WyckoffEvent(
                name="LPSY",
                desc="Pullback ideal para continuação da queda",
                price=close_now,
            )
        )
    elif phase == "Acumulação":
        events_confirmed.append(
            WyckoffEvent(
                name="ST",
                desc="Teste secundário em região de fundo",
                price=last_low,
            )
        )
        events_pending.append(
            WyckoffEvent(
                name="SOS",
                desc="Rompimento com expansão acima da faixa",
                price=last_high,
            )
        )
    elif phase == "Distribuição":
        events_confirmed.append(
            WyckoffEvent(
                name="UT",
                desc="Upthrust em região de topo",
                price=last_high,
            )
        )
        events_pending.append(
            WyckoffEvent(
                name="SOW",
                desc="Quebra da base da faixa distributiva",
                price=last_low,
            )
        )

    vol_info = _volume_state(df)

    return WyckoffData(
        phase=phase,
        progress=round(progress, 1),
        confidence=round(confidence, 1),
        next_phase=next_phase,
        composite_man=composite,
        events_confirmed=events_confirmed,
        events_pending=events_pending,
        volume_state=vol_info["volume_state"],
        volume_label=vol_info["volume_label"],
    )