from typing import Dict

import pandas as pd

from .monte_carlo import calculate_monte_carlo
from .risk import calculate_risk_metrics
from .seasonality import calculate_seasonality
from .stats import calculate_historical_stats, calculate_win_rates
from .types import (
    HistoricalStats,
    MonteCarloStats,
    ProbabilisticResult,
    RiskMetrics,
    SeasonalityItem,
)


def _build_scenarios(monte_carlo: dict, win_rate_long: float, win_rate_short: float) -> dict:
    bullish = max(1.0, min(99.0, round(win_rate_long, 1)))
    bearish = max(1.0, min(99.0, round(win_rate_short, 1)))

    neutral = max(1.0, min(99.0, round(100.0 - ((bullish + bearish) / 2), 1)))

    return {
        "bullish": bullish,
        "neutral": neutral,
        "bearish": bearish,
    }


def calculate_probabilistic(df: pd.DataFrame) -> Dict:
    if df is None or df.empty:
        return {
            "win_rate_general": 50.0,
            "win_rate_long": 50.0,
            "win_rate_short": 50.0,
            "historical": {
                "periods": 0,
                "return_pct": 0.0,
                "volatility_pct": 0.0,
                "sharpe": 0.0,
                "max_drawdown_pct": 0.0,
            },
            "monte_carlo": {
                "confidence_level": 90,
                "low": 0.0,
                "mid": 0.0,
                "high": 0.0,
            },
            "scenarios": {
                "bullish": 50.0,
                "neutral": 1.0,
                "bearish": 50.0,
            },
            "seasonality": [],
            "risk_metrics": {
                "var_95": 0.0,
                "expected_shortfall": 0.0,
                "beta": 0.0,
                "correlation": 0.0,
            },
        }

    win_general, win_long, win_short = calculate_win_rates(df)
    historical_data = calculate_historical_stats(df)
    monte_carlo_data = calculate_monte_carlo(df)
    seasonality_data = calculate_seasonality(df)
    risk_data = calculate_risk_metrics(df)
    scenarios_data = _build_scenarios(monte_carlo_data, win_long, win_short)

    result = ProbabilisticResult(
        win_rate_general=win_general,
        win_rate_long=win_long,
        win_rate_short=win_short,
        historical=HistoricalStats(**historical_data),
        monte_carlo=MonteCarloStats(**monte_carlo_data),
        scenarios=scenarios_data,
        seasonality=[SeasonalityItem(**item) for item in seasonality_data],
        risk_metrics=RiskMetrics(**risk_data),
    )

    return {
        "win_rate_general": result.win_rate_general,
        "win_rate_long": result.win_rate_long,
        "win_rate_short": result.win_rate_short,
        "historical": {
            "periods": result.historical.periods,
            "return_pct": result.historical.return_pct,
            "volatility_pct": result.historical.volatility_pct,
            "sharpe": result.historical.sharpe,
            "max_drawdown_pct": result.historical.max_drawdown_pct,
        },
        "monte_carlo": {
            "confidence_level": result.monte_carlo.confidence_level,
            "low": result.monte_carlo.low,
            "mid": result.monte_carlo.mid,
            "high": result.monte_carlo.high,
        },
        "scenarios": result.scenarios,
        "seasonality": [
            {
                "month": item.month,
                "value": item.value,
            }
            for item in result.seasonality
        ],
        "risk_metrics": {
            "var_95": result.risk_metrics.var_95,
            "expected_shortfall": result.risk_metrics.expected_shortfall,
            "beta": result.risk_metrics.beta,
            "correlation": result.risk_metrics.correlation,
        },
    }