from __future__ import annotations

from typing import List

import pandas as pd

from .types import FVGZone


def detect_fvgs(df: pd.DataFrame) -> List[FVGZone]:
    zones: List[FVGZone] = []

    for i in range(2, len(df)):
        c1 = df.iloc[i - 2]
        c2 = df.iloc[i - 1]
        c3 = df.iloc[i]

        bullish_gap = c1["high"] < c3["low"]
        bearish_gap = c1["low"] > c3["high"]

        if bullish_gap:
            low = float(c1["high"])
            high = float(c3["low"])
            filled = (df.iloc[i + 1 :]["low"] <= low).any() if i + 1 < len(df) else False
            zones.append(
                FVGZone(
                    title="Bullish FVG",
                    zone=f"{low:.2f} → {high:.2f}",
                    state="Preenchido" if filled else "Aberto",
                    bullish=True,
                )
            )

        if bearish_gap:
            low = float(c3["high"])
            high = float(c1["low"])
            filled = (df.iloc[i + 1 :]["high"] >= high).any() if i + 1 < len(df) else False
            zones.append(
                FVGZone(
                    title="Bearish FVG",
                    zone=f"{low:.2f} → {high:.2f}",
                    state="Preenchido" if filled else "Aberto",
                    bullish=False,
                )
            )

    return zones[-10:]