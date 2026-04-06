from typing import Dict, List, Optional, Tuple

from .fibonacci import safe_ratio
from .types import HarmonicPattern, HarmonicPivot, HarmonicRatioCheck


PATTERN_SPECS: Dict[str, Dict[str, Tuple[float, float]]] = {
    "Gartley": {
        "XB": (0.55, 0.70),   # ideal ~0.618
        "AC": (0.382, 0.886),
        "BD": (1.272, 1.618),
        "XD": (0.75, 0.82),   # ideal ~0.786
    },
    "Butterfly": {
        "XB": (0.75, 0.82),   # ideal ~0.786
        "AC": (0.382, 0.886),
        "BD": (1.618, 2.618),
        "XD": (1.20, 1.70),   # ideal ~1.272-1.618
    },
    "Bat": {
        "XB": (0.382, 0.55),
        "AC": (0.382, 0.886),
        "BD": (1.618, 2.618),
        "XD": (0.82, 0.93),   # ideal ~0.886
    },
    "Crab": {
        "XB": (0.382, 0.618),
        "AC": (0.382, 0.886),
        "BD": (2.24, 3.618),
        "XD": (1.50, 1.75),   # ideal ~1.618
    },
    "Shark": {
        "XB": (0.382, 0.618),
        "AC": (1.13, 1.618),
        "BD": (1.618, 2.24),
        "XD": (0.886, 1.13),
    },
    "Cypher": {
        "XB": (0.382, 0.618),
        "AC": (1.13, 1.414),
        "BD": (1.272, 2.00),
        "XD": (0.75, 0.82),   # ideal ~0.786
    },
}


PATTERN_ICONS = {
    "Gartley": "🦋",
    "Butterfly": "🦋",
    "Bat": "🦇",
    "Crab": "🦀",
    "Shark": "🦈",
    "Cypher": "🔷",
}


def _in_range(value: float, min_v: float, max_v: float) -> bool:
    return min_v <= value <= max_v


def _format_expected(spec: Tuple[float, float]) -> str:
    return f"{spec[0]:.3f}-{spec[1]:.3f}"


def _build_ratio_checks(
    xb: float,
    ac: float,
    bd: float,
    xd: float,
    specs: Dict[str, Tuple[float, float]],
) -> List[HarmonicRatioCheck]:
    values = {
        "XB": xb,
        "AC": ac,
        "BD": bd,
        "XD": xd,
    }

    checks: List[HarmonicRatioCheck] = []
    for key, value in values.items():
        min_v, max_v = specs[key]
        ok = _in_range(value, min_v, max_v)
        checks.append(
            HarmonicRatioCheck(
                key=key,
                value=f"{value:.3f}",
                expected=_format_expected((min_v, max_v)),
                ok=ok,
            )
        )

    return checks


def _confidence_from_checks(checks: List[HarmonicRatioCheck]) -> float:
    if not checks:
        return 0.0

    hits = sum(1 for item in checks if item.ok)
    base = (hits / len(checks)) * 100.0

    if hits == 4:
        return 75.0
    if hits == 3:
        return 50.0
    if hits == 2:
        return 35.0
    return max(10.0, base * 0.5)


def _direction_from_pivots(x: HarmonicPivot, a: HarmonicPivot, b: HarmonicPivot, c: HarmonicPivot, d: HarmonicPivot) -> Tuple[bool, str]:
    bullish = d.kind == "low"
    direction = "Alta" if bullish else "Baixa"
    return bullish, direction


def _compute_targets_and_stop(
    bullish: bool,
    x: HarmonicPivot,
    a: HarmonicPivot,
    b: HarmonicPivot,
    c: HarmonicPivot,
    d: HarmonicPivot,
) -> Tuple[List[float], float]:
    cd_range = abs(c.price - d.price)

    if bullish:
        target1 = d.price + cd_range * 0.382
        target2 = d.price + cd_range * 0.618
        stop = min(d.price, x.price) - (cd_range * 0.25)
    else:
        target1 = d.price - cd_range * 0.382
        target2 = d.price - cd_range * 0.618
        stop = max(d.price, x.price) + (cd_range * 0.25)

    return [float(target1), float(target2)], float(stop)


def evaluate_last_pattern(pivots: List[HarmonicPivot]) -> List[HarmonicPattern]:
    if len(pivots) < 5:
        return []

    x, a, b, c, d = pivots[-5], pivots[-4], pivots[-3], pivots[-2], pivots[-1]

    xa = a.price - x.price
    ab = b.price - a.price
    bc = c.price - b.price
    cd = d.price - c.price
    xd_move = d.price - x.price

    xb_ratio = safe_ratio(ab, xa)
    ac_ratio = safe_ratio(bc, ab)
    bd_ratio = safe_ratio(cd, bc)
    xd_ratio = safe_ratio(xd_move, xa)

    bullish, direction = _direction_from_pivots(x, a, b, c, d)

    patterns: List[HarmonicPattern] = []

    for pattern_name, specs in PATTERN_SPECS.items():
        checks = _build_ratio_checks(
            xb=xb_ratio,
            ac=ac_ratio,
            bd=bd_ratio,
            xd=xd_ratio,
            specs=specs,
        )

        confidence = _confidence_from_checks(checks)

        if confidence < 50:
            continue

        targets, stop = _compute_targets_and_stop(
            bullish=bullish,
            x=x,
            a=a,
            b=b,
            c=c,
            d=d,
        )

        prz = [float(d.price), float((c.price + d.price) / 2)]

        patterns.append(
            HarmonicPattern(
                name=pattern_name,
                direction=direction,
                confidence=round(confidence, 1),
                bullish=bullish,
                icon=PATTERN_ICONS.get(pattern_name, "⬡"),
                ratios=checks,
                prz=prz,
                targets=targets,
                stop=stop,
            )
        )

    patterns.sort(key=lambda x: x.confidence, reverse=True)
    return patterns[:4]