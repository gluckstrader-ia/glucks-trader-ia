import numpy as np
import pandas as pd


def calculate_risk_metrics(df: pd.DataFrame) -> dict:
    returns = df["close"].pct_change().dropna()

    if returns.empty:
        return {
            "var_95": 0.0,
            "expected_shortfall": 0.0,
            "beta": 0.0,
            "correlation": 0.0,
        }

    var_95 = float(np.percentile(returns, 5) * 100)

    tail_losses = returns[returns <= np.percentile(returns, 5)]
    expected_shortfall = float(tail_losses.mean() * 100) if not tail_losses.empty else var_95

    # Sem benchmark explícito no seu backend atual:
    # beta e correlation ficam neutros, não fake.
    beta = 0.0
    correlation = 0.0

    return {
        "var_95": round(var_95, 2),
        "expected_shortfall": round(expected_shortfall, 2),
        "beta": round(beta, 2),
        "correlation": round(correlation, 2),
    }