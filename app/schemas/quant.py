from pydantic import BaseModel
from typing import Optional


class QuantDashboardResponse(BaseModel):
    asset: str
    asset_type: str
    timeframe: str

    score: float
    signal: str

    short_trend: str
    mid_trend: str

    roc: float
    rsi: float
    pressure: float

    atr: float
    relative_volatility: float

    relative_volume: float
    adx: float

    updated_at: Optional[str] = None