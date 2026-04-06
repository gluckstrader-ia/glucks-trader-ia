from typing import List

import pandas as pd

from .types import FibLevel


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return abs(numerator / denominator)


def build_fib_levels(df: pd.DataFrame, lookback: int = 120) -> List[FibLevel]:
    sample = df.tail(min(lookback, len(df))).copy()

    if sample.empty:
        return []

    swing_low = float(sample["low"].min())
    swing_high = float(sample["high"].max())

    if swing_high <= swing_low:
        return []

    diff = swing_high - swing_low

    levels = [
        ("23.6%", swing_low + diff * 0.236),
        ("38.2%", swing_low + diff * 0.382),
        ("50.0%", swing_low + diff * 0.500),
        ("61.8%", swing_low + diff * 0.618),
        ("78.6%", swing_low + diff * 0.786),
        ("100.0%", swing_high),
        ("127.2%", swing_high + diff * 0.272),
        ("161.8%", swing_high + diff * 0.618),
    ]

    fibs: List[FibLevel] = []
    for level, price in levels:
        level_num = level.replace("%", "")
        kind = "support" if float(level_num) < 100 else "resistance"
        fibs.append(FibLevel(level=level, price=float(price), type=kind))

    return fibs