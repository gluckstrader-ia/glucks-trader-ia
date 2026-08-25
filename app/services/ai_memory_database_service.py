from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import AISignalMemory


# =====================================================
# AI MEMORY DATABASE SERVICE V2
# =====================================================


def save_ai_memory(
    db: Session,
    analysis: Dict[str, Any],
):
    """
    Salva uma análise da IA na tabela ai_signal_memory.
    """

    ai_brain = analysis.get(
        "ai_brain",
        {},
    )

    final_signal = analysis.get(
        "final_signal",
        {},
    )


    memory = AISignalMemory(

        asset=analysis.get(
            "asset",
            "",
        ),

        asset_type=analysis.get(
            "asset_type",
            "",
        ),

        timeframe=analysis.get(
            "timeframe",
            "",
        ),


        direction=final_signal.get(
            "direction",
            analysis.get(
                "direction",
                "NEUTRO",
            ),
        ),


        signal_confidence=ai_brain.get(
            "signal_confidence",
            "",
        ),


        trade_quality_score=ai_brain.get(
            "trade_quality_score",
            0,
        ),


        trade_quality_label=ai_brain.get(
            "trade_quality_label",
            "",
        ),


        module_alignment=ai_brain.get(
            "module_alignment",
            "",
        ),


        decision_state=ai_brain.get(
            "decision_state",
            "",
        ),


        decision_color=ai_brain.get(
            "decision_color",
            "",
        ),


        entry=final_signal.get(
            "entry"
        ),

        stop=final_signal.get(
            "stop"
        ),

        target=final_signal.get(
            "target"
        ),

    )


    db.add(memory)

    db.commit()

    db.refresh(memory)


    return memory



# =====================================================
# HISTORY
# =====================================================


def get_memory_history(
    db: Session,
    limit: int = 100,
) -> List[AISignalMemory]:

    return (
        db.query(
            AISignalMemory
        )
        .order_by(
            AISignalMemory.created_at.desc()
        )
        .limit(limit)
        .all()
    )



# =====================================================
# PATTERN SEARCH
# =====================================================


def find_database_patterns(
    db: Session,
    asset: str,
    timeframe: str,
    direction: str,
    module_alignment: str,
    limit: int = 100,
):

    return (
        db.query(
            AISignalMemory
        )
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
# MEMORY STATISTICS
# =====================================================


def calculate_database_memory_statistics(
    db: Session,
    asset: Optional[str] = None,
):

    query = db.query(
        AISignalMemory
    )


    if asset:

        query = query.filter(
            AISignalMemory.asset == asset
        )


    records = query.all()


    total = len(records)


    wins = len(
        [
            item
            for item in records
            if item.result == "WIN"
        ]
    )


    losses = len(
        [
            item
            for item in records
            if item.result == "LOSS"
        ]
    )


    closed = wins + losses


    win_rate = 0


    if closed > 0:

        win_rate = round(
            wins / closed * 100,
            1,
        )


    return {

        "total_signals": total,

        "closed_signals": closed,

        "wins": wins,

        "losses": losses,

        "win_rate": win_rate,

    } 