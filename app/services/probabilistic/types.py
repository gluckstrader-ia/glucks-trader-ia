from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class HistoricalStats:
    periods: int
    return_pct: float
    volatility_pct: float
    sharpe: float
    max_drawdown_pct: float


@dataclass
class MonteCarloStats:
    confidence_level: int
    low: float
    mid: float
    high: float


@dataclass
class SeasonalityItem:
    month: str
    value: float


@dataclass
class RiskMetrics:
    var_95: float
    expected_shortfall: float
    beta: float
    correlation: float


@dataclass
class ProbabilisticResult:
    win_rate_general: float
    win_rate_long: float
    win_rate_short: float
    historical: HistoricalStats
    monte_carlo: MonteCarloStats
    scenarios: Dict[str, float]
    seasonality: List[SeasonalityItem] = field(default_factory=list)
    risk_metrics: RiskMetrics = None