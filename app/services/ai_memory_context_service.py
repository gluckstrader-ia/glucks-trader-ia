from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models import AISignalMemory


# =====================================================
# AI MEMORY CONTEXT SERVICE
# =====================================================


def get_similar_memory_cases(
    db: Session,
    asset: str,
    timeframe: str,
    direction: str,
    module_alignment: str,
    limit: int = 100,
) -> List[AISignalMemory]:
    """
    Busca cenários históricos semelhantes ao cenário atual.
    """

    return (
        db.query(AISignalMemory)
        .filter(
            AISignalMemory.asset == asset,
            AISignalMemory.timeframe == timeframe,
            AISignalMemory.direction == direction,
            AISignalMemory.module_alignment == module_alignment,
        )
        .order_by(
            AISignalMemory.created_at.desc()
        )
        .limit(limit)
        .all()
    )


# =====================================================
# HISTORICAL PERFORMANCE
# =====================================================


def calculate_memory_statistics(
    cases: List[AISignalMemory],
) -> Dict[str, Any]:

    total = len(cases)

    wins = len(
        [
            item
            for item in cases
            if item.result == "WIN"
        ]
    )

    losses = len(
        [
            item
            for item in cases
            if item.result == "LOSS"
        ]
    )


    closed = wins + losses


    win_rate = 0

    if closed > 0:
        win_rate = round(
            (wins / closed) * 100,
            1,
        )


    if win_rate >= 65:
        bias = "FAVORAVEL"

    elif win_rate <= 45:
        bias = "DESFAVORAVEL"

    else:
        bias = "NEUTRO"


    return {

        "similar_cases": total,

        "closed_cases": closed,

        "wins": wins,

        "losses": losses,

        "win_rate": win_rate,

        "memory_bias": bias,

    }



# =====================================================
# BUILD MEMORY CONTEXT
# =====================================================


def build_memory_context(
    db: Session,
    analysis: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Cria o contexto histórico para a decisão da IA.
    """

    ai_brain = analysis.get(
        "ai_brain",
        {},
    )


    asset = analysis.get(
        "asset",
        "",
    )


    timeframe = analysis.get(
        "timeframe",
        "",
    )


    direction = analysis.get(
        "direction",
        "NEUTRO",
    )


    module_alignment = ai_brain.get(
        "module_alignment",
        "",
    )


    cases = get_similar_memory_cases(
        db,
        asset,
        timeframe,
        direction,
        module_alignment,
    )


    statistics = calculate_memory_statistics(
        cases
    )


    return {

        "asset": asset,

        "timeframe": timeframe,

        "direction": direction,

        "module_alignment": module_alignment,

        **statistics,

    }