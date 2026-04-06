from typing import Dict

import pandas as pd

from .dow import calculate_dow
from .elliott import calculate_elliott
from .gann import calculate_gann
from .types import WegdResult
from .wyckoff import calculate_wyckoff


def _module_bias(label: str) -> str:
    v = (label or "").upper()

    if v in {"MARKUP", "ACUMULAÇÃO", "EXPANSÃO", "ALTA", "BULLISH"}:
        return "COMPRA"
    if v in {"MARKDOWN", "DISTRIBUIÇÃO", "BAIXA", "BEARISH"}:
        return "VENDA"
    return "NEUTRO"


def _resolve_bias(wyckoff_phase: str, elliott_mode: str, dow_primary: str) -> str:
    votes = []

    votes.append(_module_bias(wyckoff_phase))
    votes.append("COMPRA" if (elliott_mode or "").upper() == "IMPULSIVA" else "VENDA" if (elliott_mode or "").upper() == "CORRETIVA" else "NEUTRO")
    votes.append("COMPRA" if (dow_primary or "").upper() == "ALTA" else "VENDA" if (dow_primary or "").upper() == "BAIXA" else "NEUTRO")

    buy = votes.count("COMPRA")
    sell = votes.count("VENDA")

    if buy > sell:
        return "COMPRA"
    if sell > buy:
        return "VENDA"
    return "NEUTRO"


def _confluence_label(bias: str, wyckoff_phase: str, elliott_mode: str, dow_primary: str) -> str:
    wy = _module_bias(wyckoff_phase)
    el = "COMPRA" if (elliott_mode or "").upper() == "IMPULSIVA" else "VENDA" if (elliott_mode or "").upper() == "CORRETIVA" else "NEUTRO"
    dw = "COMPRA" if (dow_primary or "").upper() == "ALTA" else "VENDA" if (dow_primary or "").upper() == "BAIXA" else "NEUTRO"

    aligned = sum(1 for x in [wy, el, dw] if x == bias and bias != "NEUTRO")

    if bias == "NEUTRO":
        return "3/10"
    if aligned == 3:
        return "8/10"
    if aligned == 2:
        return "6/10"
    return "4/10"


def _summary(wyckoff, elliott, gann, dow, bias: str) -> str:
    return (
        f"Wyckoff: {wyckoff.phase}, "
        f"Elliott: {elliott.current_wave}, "
        f"Gann: {gann.dominant_angle}, "
        f"Dow: {dow.primary}. "
        f"Confluência {bias}."
    )


def calculate_wegd(df: pd.DataFrame) -> Dict:
    last = df.iloc[-1]

    close_now = float(last["close"])
    sma20 = float(df["close"].tail(20).mean()) if len(df) >= 20 else close_now
    sma50 = float(df["close"].tail(50).mean()) if len(df) >= 50 else sma20

    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0).tail(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).tail(14).mean()
    rs = gain / loss if loss and loss != 0 else 0
    rsi = 100 - (100 / (1 + rs)) if rs != 0 else 50.0

    wyckoff = calculate_wyckoff(
        df=df,
        close_now=close_now,
        sma20=sma20,
        sma50=sma50,
        rsi=rsi,
    )
    elliott = calculate_elliott(df)
    gann = calculate_gann(df)
    dow = calculate_dow(df)

    bias = _resolve_bias(
        wyckoff_phase=wyckoff.phase,
        elliott_mode=elliott.mode,
        dow_primary=dow.primary,
    )

    confluence = _confluence_label(
        bias=bias,
        wyckoff_phase=wyckoff.phase,
        elliott_mode=elliott.mode,
        dow_primary=dow.primary,
    )

    result = WegdResult(
        bias=bias,
        confluence=confluence,
        summary=_summary(wyckoff, elliott, gann, dow, bias),
        wyckoff=wyckoff,
        elliott=elliott,
        gann=gann,
        dow=dow,
    )

    return {
        "bias": result.bias,
        "confluence": result.confluence,
        "summary": result.summary,
        "wyckoff": {
            "phase": result.wyckoff.phase,
            "progress": result.wyckoff.progress,
            "confidence": result.wyckoff.confidence,
            "next_phase": result.wyckoff.next_phase,
            "composite_man": result.wyckoff.composite_man,
            "events_confirmed": [
                {
                    "name": x.name,
                    "desc": x.desc,
                    "price": x.price,
                }
                for x in result.wyckoff.events_confirmed
            ],
            "events_pending": [
                {
                    "name": x.name,
                    "desc": x.desc,
                    "price": x.price,
                }
                for x in result.wyckoff.events_pending
            ],
            "volume_state": result.wyckoff.volume_state,
            "volume_label": result.wyckoff.volume_label,
        },
        "elliott": {
            "current_wave": result.elliott.current_wave,
            "mode": result.elliott.mode,
            "progress": result.elliott.progress,
            "confidence": result.elliott.confidence,
            "next_wave": result.elliott.next_wave,
            "invalidation": result.elliott.invalidation,
            "wave_points": [
                {
                    "label": x.label,
                    "price": x.price,
                    "type": x.type,
                }
                for x in result.elliott.wave_points
            ],
        },
        "gann": {
            "dominant_angle": result.gann.dominant_angle,
            "support_angles": [
                {"angle": x.angle, "price": x.price}
                for x in result.gann.support_angles
            ],
            "resistance_angles": [
                {"angle": x.angle, "price": x.price}
                for x in result.gann.resistance_angles
            ],
            "current_cycle_days": result.gann.current_cycle_days,
            "next_reversal": result.gann.next_reversal,
            "days_in_cycle": result.gann.days_in_cycle,
            "price_square_levels": [
                {"price": x.price, "strength": x.strength}
                for x in result.gann.price_square_levels
            ],
        },
        "dow": {
            "primary": result.dow.primary,
            "secondary": result.dow.secondary,
            "minor": result.dow.minor,
            "market_phase": result.dow.market_phase,
            "market_phase_score": result.dow.market_phase_score,
            "price_volume_confirmation": result.dow.price_volume_confirmation,
            "indices_confirmation": result.dow.indices_confirmation,
            "volume_note": result.dow.volume_note,
        },
    }