from typing import Tuple

import numpy as np
import pandas as pd


def close_returns(df: pd.DataFrame) -> pd.Series:
    returns = df["close"].pct_change().dropna()
    return returns.replace([np.inf, -np.inf], np.nan).dropna()


def calculate_win_rates(df: pd.DataFrame) -> Tuple[float, float, float]:
    returns = close_returns(df)

    if returns.empty:
        return 50.0, 50.0, 50.0

    general = float((returns > 0).mean() * 100)

    up_moves = returns[returns > 0]
    down_moves = returns[returns < 0]

    long_rate = float((up_moves.count() / len(returns)) * 100) if len(returns) else 50.0
    short_rate = float((down_moves.count() / len(returns)) * 100) if len(returns) else 50.0

    return round(general, 1), round(long_rate, 1), round(short_rate, 1)


def calculate_historical_stats(df: pd.DataFrame) -> dict:
    returns = close_returns(df)

    if returns.empty:
        return {
            "periods": 0,
            "return_pct": 0.0,
            "volatility_pct": 0.0,
            "sharpe": 0.0,
            "max_drawdown_pct": 0.0,
        }

    periods = int(len(returns))
    cumulative_return = float(((1 + returns).prod() - 1) * 100)
    volatility_pct = float(returns.std(ddof=0) * 100)

    mean_ret = float(returns.mean())
    std_ret = float(returns.std(ddof=0))
    sharpe = (mean_ret / std_ret) if std_ret > 0 else 0.0

    equity_curve = (1 + returns).cumprod()
    rolling_max = equity_curve.cummax()
    drawdown = (equity_curve / rolling_max) - 1.0
    max_drawdown_pct = float(abs(drawdown.min()) * 100) if not drawdown.empty else 0.0

    return {
        "periods": periods,
        "return_pct": round(cumulative_return, 2),
        "volatility_pct": round(volatility_pct, 2),
        "sharpe": round(sharpe, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 2),
    }