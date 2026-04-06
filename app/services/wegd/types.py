from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class WyckoffEvent:
    name: str
    desc: str
    price: float


@dataclass
class WyckoffData:
    phase: str
    progress: float
    confidence: float
    next_phase: str
    composite_man: str
    events_confirmed: List[WyckoffEvent] = field(default_factory=list)
    events_pending: List[WyckoffEvent] = field(default_factory=list)
    volume_state: str = "Normal"
    volume_label: str = "Médio"


@dataclass
class ElliottWavePoint:
    label: str
    price: float
    type: str


@dataclass
class ElliottData:
    current_wave: str
    mode: str
    progress: float
    confidence: float
    next_wave: str
    invalidation: float
    wave_points: List[ElliottWavePoint] = field(default_factory=list)


@dataclass
class GannAngle:
    angle: str
    price: float


@dataclass
class GannPriceLevel:
    price: float
    strength: str


@dataclass
class GannData:
    dominant_angle: str
    support_angles: List[GannAngle] = field(default_factory=list)
    resistance_angles: List[GannAngle] = field(default_factory=list)
    current_cycle_days: int = 0
    next_reversal: str = ""
    days_in_cycle: int = 0
    price_square_levels: List[GannPriceLevel] = field(default_factory=list)


@dataclass
class DowData:
    primary: str
    secondary: str
    minor: str
    market_phase: str
    market_phase_score: float
    price_volume_confirmation: str
    indices_confirmation: str
    volume_note: str


@dataclass
class WegdResult:
    bias: str
    confluence: str
    summary: str
    wyckoff: WyckoffData
    elliott: ElliottData
    gann: GannData
    dow: DowData