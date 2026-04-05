from __future__ import annotations

import pandas as pd

from .fvg import detect_fvgs
from .liquidity import detect_liquidity
from .order_blocks import detect_order_blocks
from .structure import (
    classify_structure,
    detect_structure_breaks,
    find_swings,
    infer_bias_from_structure,
)
from .types import SmcResult, SmcWindowSummary


def _window_bias(df: pd.DataFrame, candles: int) -> SmcWindowSummary:
    sample = df.tail(candles).copy()

    if len(sample) < 10:
        return SmcWindowSummary(candles=candles, bias="NEUTRO")

    first_close = float(sample["close"].iloc[0])
    last_close = float(sample["close"].iloc[-1])

    if last_close > first_close:
        bias = "ALTA"
    elif last_close < first_close:
        bias = "BAIXA"
    else:
        bias = "LATERAL"

    return SmcWindowSummary(candles=candles, bias=bias)


def _detect_divergence(context: SmcWindowSummary, structure: SmcWindowSummary, trigger: SmcWindowSummary) -> str:
    values = [context.bias, structure.bias, trigger.bias]
    unique = set(values)

    if len(unique) == 1:
        return "Sem divergência relevante"

    return f"MACRO {context.bias}, MÉDIO {structure.bias}, MICRO {trigger.bias} - Aguardar confirmação"


def _build_summary(
    bias: str,
    structure_label: str,
    last_bos: float | None,
    order_blocks_count: int,
    fvg_open_count: int,
    divergence: str,
) -> str:
    bos_text = f"{last_bos:.2f}" if isinstance(last_bos, (int, float)) else "não identificado"

    return (
        f"Viés Institucional: {bias}. "
        f"{structure_label}. "
        f"Último BOS em {bos_text}. "
        f"{order_blocks_count} Order Blocks ativos, "
        f"{fvg_open_count} FVGs não preenchidos. "
        f"Divergência: {divergence}"
    )


def calculate_smc(df: pd.DataFrame) -> dict:
    swings = find_swings(df, left=3, right=3)
    structure_label = classify_structure(swings)
    bias = infer_bias_from_structure(structure_label)

    structure_breaks, last_bos = detect_structure_breaks(df, swings)
    order_blocks = detect_order_blocks(df)
    fvgs = detect_fvgs(df)
    liquidity = detect_liquidity(df)

    context = _window_bias(df, 300)
    structure = _window_bias(df, 80)
    trigger = _window_bias(df, 20)

    divergence = _detect_divergence(context, structure, trigger)

    open_fvgs = sum(1 for item in fvgs if item.state.upper() == "ABERTO")

    summary = _build_summary(
        bias=bias,
        structure_label=structure_label,
        last_bos=last_bos,
        order_blocks_count=len(order_blocks),
        fvg_open_count=open_fvgs,
        divergence=divergence,
    )

    result = SmcResult(
        bias=bias,
        structure_label=structure_label,
        last_bos=last_bos,
        context=context,
        structure=structure,
        trigger=trigger,
        divergence=divergence,
        order_blocks=order_blocks,
        fvgs=fvgs,
        liquidity=liquidity,
        structure_breaks=structure_breaks,
        summary=summary,
    )

    return {
        "bias": result.bias,
        "structure_label": result.structure_label,
        "last_bos": result.last_bos,
        "context": {
            "candles": result.context.candles,
            "bias": result.context.bias,
        },
        "structure": {
            "candles": result.structure.candles,
            "bias": result.structure.bias,
        },
        "trigger": {
            "candles": result.trigger.candles,
            "bias": result.trigger.bias,
        },
        "divergence": result.divergence,
        "order_blocks": [
            {
                "title": x.title,
                "price": x.price,
                "desc": x.desc,
                "strength": x.strength,
                "bullish": x.bullish,
            }
            for x in result.order_blocks
        ],
        "fvgs": [
            {
                "title": x.title,
                "zone": x.zone,
                "state": x.state,
                "bullish": x.bullish,
            }
            for x in result.fvgs
        ],
        "liquidity": [
            {
                "price": x.price,
                "desc": x.desc,
                "tag": x.tag,
            }
            for x in result.liquidity
        ],
        "structure_breaks": [
            {
                "title": x.title,
                "price": x.price,
                "desc": x.desc,
                "bullish": x.bullish,
            }
            for x in result.structure_breaks
        ],
        "summary": result.summary,
    }