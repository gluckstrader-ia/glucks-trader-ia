from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SwingPoint:
    index: int
    price: float
    kind: str  # "high" | "low"


@dataclass
class StructureBreak:
    title: str
    price: float
    desc: str
    bullish: bool


@dataclass
class OrderBlock:
    title: str
    price: str
    desc: str
    strength: str
    bullish: bool


@dataclass
class FVGZone:
    title: str
    zone: str
    state: str
    bullish: bool


@dataclass
class LiquidityZone:
    price: float
    desc: str
    tag: str


@dataclass
class SmcWindowSummary:
    candles: int
    bias: str


@dataclass
class SmcResult:
    bias: str
    structure_label: str
    last_bos: Optional[float]
    context: SmcWindowSummary
    structure: SmcWindowSummary
    trigger: SmcWindowSummary
    divergence: str
    order_blocks: List[OrderBlock] = field(default_factory=list)
    fvgs: List[FVGZone] = field(default_factory=list)
    liquidity: List[LiquidityZone] = field(default_factory=list)
    structure_breaks: List[StructureBreak] = field(default_factory=list)
    summary: str = ""