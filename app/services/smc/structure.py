from __future__ import annotations

from typing import List, Tuple

import pandas as pd

from .types import SwingPoint, StructureBreak


def find_swings(df: pd.DataFrame, left: int = 3, right: int = 3) -> List[SwingPoint]:
    swings: List[SwingPoint] = []

    highs = df["high"].tolist()
    lows = df["low"].tolist()

    for i in range(left, len(df) - right):
        high = highs[i]
        low = lows[i]

        is_swing_high = all(high > highs[j] for j in range(i - left, i)) and all(
            high >= highs[j] for j in range(i + 1, i + right + 1)
        )
        is_swing_low = all(low < lows[j] for j in range(i - left, i)) and all(
            low <= lows[j] for j in range(i + 1, i + right + 1)
        )

        if is_swing_high:
            swings.append(SwingPoint(index=i, price=float(high), kind="high"))
        if is_swing_low:
            swings.append(SwingPoint(index=i, price=float(low), kind="low"))

    swings.sort(key=lambda x: x.index)
    return swings


def classify_structure(swings: List[SwingPoint]) -> str:
    highs = [s for s in swings if s.kind == "high"]
    lows = [s for s in swings if s.kind == "low"]

    if len(highs) < 2 or len(lows) < 2:
        return "Estrutura indefinida"

    last_high, prev_high = highs[-1], highs[-2]
    last_low, prev_low = lows[-1], lows[-2]

    hh = last_high.price > prev_high.price
    hl = last_low.price > prev_low.price
    lh = last_high.price < prev_high.price
    ll = last_low.price < prev_low.price

    if hh and hl:
        return "Estrutura HH/HL (Tendência de Alta)"
    if lh and ll:
        return "Estrutura LH/LL (Tendência de Baixa)"
    return "Estrutura Lateral"


def infer_bias_from_structure(structure_label: str) -> str:
    label = structure_label.upper()
    if "HH/HL" in label or "ALTA" in label:
        return "BULLISH"
    if "LH/LL" in label or "BAIXA" in label:
        return "BEARISH"
    return "NEUTRO"


def detect_structure_breaks(
    df: pd.DataFrame, swings: List[SwingPoint]
) -> Tuple[List[StructureBreak], float | None]:
    events: List[StructureBreak] = []
    last_bos = None

    closes = df["close"].tolist()

    for swing in swings[-12:]:
        if swing.kind == "high":
            broken = any(c > swing.price for c in closes[swing.index + 1 :])
            if broken:
                events.append(
                    StructureBreak(
                        title="Break of Structure",
                        price=swing.price,
                        desc=f"BOS Alta: rompimento acima de {swing.price:.2f}",
                        bullish=True,
                    )
                )
                last_bos = swing.price

        elif swing.kind == "low":
            broken = any(c < swing.price for c in closes[swing.index + 1 :])
            if broken:
                events.append(
                    StructureBreak(
                        title="Break of Structure",
                        price=swing.price,
                        desc=f"BOS Baixa: rompimento abaixo de {swing.price:.2f}",
                        bullish=False,
                    )
                )
                last_bos = swing.price

    return events[-6:], last_bos