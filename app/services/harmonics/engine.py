from typing import Dict

import pandas as pd

from .fibonacci import build_fib_levels
from .patterns import evaluate_last_pattern
from .pivots import find_pivots
from .types import HarmonicsResult


def calculate_harmonics(df: pd.DataFrame) -> Dict:
    if df is None or df.empty:
        return {"patterns": [], "fib_levels": []}

    pivots = find_pivots(df, left=3, right=3)
    patterns = evaluate_last_pattern(pivots)
    fib_levels = build_fib_levels(df, lookback=120)

    result = HarmonicsResult(
        patterns=patterns,
        fib_levels=fib_levels,
    )

    return {
        "patterns": [
            {
                "name": item.name,
                "direction": item.direction,
                "confidence": item.confidence,
                "bullish": item.bullish,
                "icon": item.icon,
                "ratios": [
                    {
                        "key": ratio.key,
                        "value": ratio.value,
                        "expected": ratio.expected,
                        "ok": ratio.ok,
                    }
                    for ratio in item.ratios
                ],
                "prz": item.prz,
                "targets": item.targets,
                "stop": item.stop,
            }
            for item in result.patterns
        ],
        "fib_levels": [
            {
                "level": fib.level,
                "price": fib.price,
                "type": fib.type,
            }
            for fib in result.fib_levels
        ],
    }