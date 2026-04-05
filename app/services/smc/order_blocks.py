from __future__ import annotations

from typing import List

import pandas as pd

from .types import OrderBlock


def detect_order_blocks(df: pd.DataFrame) -> List[OrderBlock]:
    obs: List[OrderBlock] = []

    for i in range(2, len(df) - 1):
        prev_candle = df.iloc[i - 1]
        curr_candle = df.iloc[i]
        next_candles = df.iloc[i + 1 : i + 6]

        bullish_impulse = (
            prev_candle["close"] < prev_candle["open"]
            and curr_candle["close"] > curr_candle["high"] - (curr_candle["high"] - curr_candle["low"]) * 0.25
        )

        bearish_impulse = (
            prev_candle["close"] > prev_candle["open"]
            and curr_candle["close"] < curr_candle["low"] + (curr_candle["high"] - curr_candle["low"]) * 0.25
        )

        if bullish_impulse:
            low = float(prev_candle["low"])
            high = float(prev_candle["high"])
            mitigated = (next_candles["low"] <= high).any()
            obs.append(
                OrderBlock(
                    title="Bullish OB (Mitigado)" if mitigated else "Bullish OB",
                    price=f"{low:.2f} - {high:.2f}",
                    desc=f"OB Bullish {low:.2f}-{high:.2f} | {'Mitigado' if mitigated else 'Ativo'}",
                    strength="78%",
                    bullish=True,
                )
            )

        if bearish_impulse:
            low = float(prev_candle["low"])
            high = float(prev_candle["high"])
            mitigated = (next_candles["high"] >= low).any()
            obs.append(
                OrderBlock(
                    title="Bearish OB (Mitigado)" if mitigated else "Bearish OB",
                    price=f"{low:.2f} - {high:.2f}",
                    desc=f"OB Bearish {low:.2f}-{high:.2f} | {'Mitigado' if mitigated else 'Ativo'}",
                    strength="78%",
                    bullish=False,
                )
            )

    return obs[-6:]