from typing import Optional

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import AISignalMemory


# =====================================================
# AI TRADE OUTCOME SERVICE
# =====================================================


def close_trade_memory(
    db: Session,
    memory_id: int,
    result: str,
    profit_points: float,
):
    """
    Atualiza o resultado final de um sinal salvo na memória.
    """

    memory = (
        db.query(AISignalMemory)
        .filter(
            AISignalMemory.id == memory_id
        )
        .first()
    )

    if not memory:
        return None


    result = str(
        result
    ).upper()


    if result not in [
        "WIN",
        "LOSS",
    ]:
        raise ValueError(
            "Resultado deve ser WIN ou LOSS"
        )


    memory.result = result

    memory.profit_points = profit_points

    memory.closed_at = datetime.utcnow()


    db.commit()

    db.refresh(memory)


    return memory



# =====================================================
# FIND OPEN TRADES
# =====================================================


def get_open_memory_trades(
    db: Session,
    limit: int = 100,
):

    return (
        db.query(AISignalMemory)
        .filter(
            AISignalMemory.result.is_(None)
        )
        .order_by(
            AISignalMemory.created_at.asc()
        )
        .limit(limit)
        .all()
    )



# =====================================================
# MEMORY PERFORMANCE
# =====================================================


def get_memory_performance(
    db: Session,
    asset: Optional[str] = None,
):

    query = db.query(
        AISignalMemory
    ).filter(
        AISignalMemory.result.isnot(None)
    )


    if asset:

        query = query.filter(
            AISignalMemory.asset == asset
        )


    trades = query.all()


    total = len(trades)


    wins = len(
        [
            trade
            for trade in trades
            if trade.result == "WIN"
        ]
    )


    losses = len(
        [
            trade
            for trade in trades
            if trade.result == "LOSS"
        ]
    )


    win_rate = 0

    if total:

        win_rate = round(
            wins / total * 100,
            1,
        )


    return {

        "total_closed": total,

        "wins": wins,

        "losses": losses,

        "win_rate": win_rate,

    }