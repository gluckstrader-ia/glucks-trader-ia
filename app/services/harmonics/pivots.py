from typing import List

import pandas as pd

from .types import HarmonicPivot


def find_pivots(df: pd.DataFrame, left: int = 3, right: int = 3) -> List[HarmonicPivot]:
    pivots: List[HarmonicPivot] = []

    highs = df["high"].tolist()
    lows = df["low"].tolist()

    for i in range(left, len(df) - right):
        high = highs[i]
        low = lows[i]

        is_pivot_high = all(high > highs[j] for j in range(i - left, i)) and all(
            high >= highs[j] for j in range(i + 1, i + right + 1)
        )
        is_pivot_low = all(low < lows[j] for j in range(i - left, i)) and all(
            low <= lows[j] for j in range(i + 1, i + right + 1)
        )

        if is_pivot_high:
            pivots.append(HarmonicPivot(index=i, price=float(high), kind="high"))
        if is_pivot_low:
            pivots.append(HarmonicPivot(index=i, price=float(low), kind="low"))

    pivots.sort(key=lambda x: x.index)
    return pivots


def get_last_five_alternating_pivots(pivots: List[HarmonicPivot]) -> List[HarmonicPivot]:
    if len(pivots) < 5:
        return []

    selected: List[HarmonicPivot] = [pivots[-1]]

    for pivot in reversed(pivots[:-1]):
        if pivot.kind != selected[-1].kind:
            selected.append(pivot)
        if len(selected) == 5:
            break

    if len(selected) < 5:
        return []

    return list(reversed(selected))