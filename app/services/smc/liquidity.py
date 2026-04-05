from __future__ import annotations

from typing import List

import pandas as pd

from .types import LiquidityZone


def detect_liquidity(df: pd.DataFrame, tolerance_pct: float = 0.0015) -> List[LiquidityZone]:
    zones: List[LiquidityZone] = []

    highs = df["high"].tolist()
    lows = df["low"].tolist()

    for i in range(1, len(highs)):
        prev_h = highs[i - 1]
        curr_h = highs[i]
        if prev_h != 0 and abs(curr_h - prev_h) / prev_h <= tolerance_pct:
            zones.append(
                LiquidityZone(
                    price=float(curr_h),
                    desc=f"BSL (Equal Highs) em {curr_h:.2f} - Stops de vendedores acumulados",
                    tag="ALTA",
                )
            )

        prev_l = lows[i - 1]
        curr_l = lows[i]
        if prev_l != 0 and abs(curr_l - prev_l) / prev_l <= tolerance_pct:
            zones.append(
                LiquidityZone(
                    price=float(curr_l),
                    desc=f"SSL (Equal Lows) em {curr_l:.2f} - Stops de compradores acumulados",
                    tag="ALTA",
                )
            )

    return zones[-8:]