from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class HarmonicPivot:
    index: int
    price: float
    kind: str  # "high" | "low"


@dataclass
class HarmonicRatioCheck:
    key: str
    value: str
    expected: str
    ok: bool


@dataclass
class HarmonicPattern:
    name: str
    direction: str
    confidence: float
    bullish: bool
    icon: str
    ratios: List[HarmonicRatioCheck] = field(default_factory=list)
    prz: List[float] = field(default_factory=list)
    targets: List[float] = field(default_factory=list)
    stop: Optional[float] = None


@dataclass
class FibLevel:
    level: str
    price: float
    type: str  # "support" | "resistance"


@dataclass
class HarmonicsResult:
    patterns: List[HarmonicPattern] = field(default_factory=list)
    fib_levels: List[FibLevel] = field(default_factory=list)