import numpy as np
import pandas as pd


def calculate_monte_carlo(
    df: pd.DataFrame,
    simulations: int = 3000,
    horizon: int = 20,
    confidence_level: int = 90,
) -> dict:
    returns = df["close"].pct_change().dropna().values

    if len(returns) < 20:
        last_price = float(df["close"].iloc[-1])
        return {
            "confidence_level": confidence_level,
            "low": round(last_price * 0.99, 6),
            "mid": round(last_price, 6),
            "high": round(last_price * 1.01, 6),
        }

    last_price = float(df["close"].iloc[-1])

    sims = []
    for _ in range(simulations):
        sampled = np.random.choice(returns, size=horizon, replace=True)
        final_price = last_price * float(np.prod(1 + sampled))
        sims.append(final_price)

    sims = np.array(sims)

    low_q = (100 - confidence_level) / 2
    high_q = 100 - low_q

    low = float(np.percentile(sims, low_q))
    mid = float(np.percentile(sims, 50))
    high = float(np.percentile(sims, high_q))

    return {
        "confidence_level": confidence_level,
        "low": round(low, 6),
        "mid": round(mid, 6),
        "high": round(high, 6),
    }