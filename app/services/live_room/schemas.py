from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


LiveSignal = Literal["buy", "sell", "neutral", "wait"]
AlertType = Literal[
    "entry_alert",
    "stop_threat",
    "target_near",
    "direction_change",
    "strengthening",
    "weakening",
    "neutral",
]


class LiveRoomStateFlags(BaseModel):
    above_vwap: bool = False
    trend_up: bool = False
    trend_down: bool = False
    lateralized: bool = True
    exhaustion: bool = False


class LiveRoomAlert(BaseModel):
    type: AlertType
    title: str
    message: str
    priority: int = Field(default=1, ge=1, le=5)


class LiveRoomScenarioMemory(BaseModel):
    previous_signal: Optional[LiveSignal] = None
    current_signal: LiveSignal
    changed: bool = False
    previous_confidence: Optional[int] = None
    current_confidence: int
    confidence_delta: int = 0
    evolution_label: str = "cenário inicial"


class LiveRoomResponse(BaseModel):
    asset: str
    timeframe: str = "5m"
    price: float
    signal: LiveSignal = "wait"
    confidence: int = Field(default=50, ge=0, le=100)
    market_regime: str = "neutral"
    narration_text: str
    entry: Optional[float] = None
    stop: Optional[float] = None
    target_1: Optional[float] = None
    target_2: Optional[float] = None
    risk_reward: Optional[float] = None
    events: List[str] = []
    alerts: List[LiveRoomAlert] = []
    scenario_memory: LiveRoomScenarioMemory
    state_flags: LiveRoomStateFlags = LiveRoomStateFlags()
    updated_at: datetime