import math
from typing import List

import pandas as pd

from .types import GannAngle, GannData, GannPriceLevel


def _gann_levels(close_now: float) -> List[GannPriceLevel]:
    root = math.sqrt(max(close_now, 0.0001))

    offsets = [
        (-0.5, "Fraco"),
        (0.0, "Moderado"),
        (0.5, "Forte"),
        (1.0, "Forte"),
    ]

    levels = []
    for offset, strength in offsets:
        price = (root + offset) ** 2
        levels.append(GannPriceLevel(price=round(price, 6), strength=strength))

    levels.sort(key=lambda x: x.price)
    return levels


def calculate_gann(df: pd.DataFrame) -> GannData:
    close_now = float(df["close"].iloc[-1])

    support_angles = [
        GannAngle(angle="1x8", price=round(close_now * 0.965, 6)),
        GannAngle(angle="1x4", price=round(close_now * 0.985, 6)),
        GannAngle(angle="1x3", price=round(close_now * 0.995, 6)),
    ]

    resistance_angles = [
        GannAngle(angle="1x8", price=round(close_now * 1.035, 6)),
        GannAngle(angle="1x4", price=round(close_now * 1.015, 6)),
        GannAngle(angle="1x3", price=round(close_now * 1.005, 6)),
    ]

    current_cycle_days = min(7, len(df))
    days_in_cycle = min(7, len(df))
    next_reversal = f"~{max(7, len(df.tail(30)))} períodos ({current_cycle_days} dias)"

    return GannData(
        dominant_angle="1x1",
        support_angles=support_angles,
        resistance_angles=resistance_angles,
        current_cycle_days=current_cycle_days,
        next_reversal=next_reversal,
        days_in_cycle=days_in_cycle,
        price_square_levels=_gann_levels(close_now),
    )