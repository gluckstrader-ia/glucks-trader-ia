from typing import List

import pandas as pd

from .types import ElliottData, ElliottWavePoint


def calculate_elliott(df: pd.DataFrame) -> ElliottData:
    sample = df.tail(min(120, len(df))).copy()

    highs = sample["high"].nlargest(min(4, len(sample))).sort_index()
    lows = sample["low"].nsmallest(min(3, len(sample))).sort_index()

    points: List[ElliottWavePoint] = []

    labels = ["1", "2", "3", "4", "5", "A", "B"]
    combined = []

    for idx, value in highs.items():
        combined.append((idx, float(value), "green"))
    for idx, value in lows.items():
        combined.append((idx, float(value), "yellow"))

    combined.sort(key=lambda x: x[0])
    combined = combined[-7:]

    for i, (_, price, point_type) in enumerate(combined):
        points.append(
            ElliottWavePoint(
                label=labels[i] if i < len(labels) else f"P{i+1}",
                price=price,
                type=point_type,
            )
        )

    if len(sample) < 30:
        current_wave = "X"
        mode = "NEUTRA"
        progress = 50.0
        confidence = 40.0
        next_wave = "—"
    else:
        start_close = float(sample["close"].iloc[0])
        end_close = float(sample["close"].iloc[-1])

        if end_close > start_close:
            current_wave = "3"
            mode = "IMPULSIVA"
            progress = 68.0
            confidence = 72.0
            next_wave = "4"
        elif end_close < start_close:
            current_wave = "C"
            mode = "CORRETIVA"
            progress = 66.0
            confidence = 68.0
            next_wave = "—"
        else:
            current_wave = "B"
            mode = "CORRETIVA"
            progress = 55.0
            confidence = 50.0
            next_wave = "C"

    invalidation = float(sample["low"].tail(20).min()) if end_close >= start_close else float(
        sample["high"].tail(20).max()
    )

    return ElliottData(
        current_wave=current_wave,
        mode=mode,
        progress=round(progress, 1),
        confidence=round(confidence, 1),
        next_wave=next_wave,
        invalidation=round(invalidation, 6),
        wave_points=points,
    )