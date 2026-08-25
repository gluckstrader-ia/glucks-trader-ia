from typing import Dict, Any, List

from sqlalchemy.orm import Session

from app.models import AISignalMemory
from app.services.ai_trade_outcome_service import close_trade_memory


# =====================================================
# AI TRADE MONITOR SERVICE
# =====================================================


def check_trade_target_stop(
    trade: AISignalMemory,
    current_price: float,
) -> Dict[str, Any]:
    """
    Verifica se uma operação aberta atingiu alvo ou stop.
    """

    direction = str(
        trade.direction
    ).upper()


    # COMPRA
    if direction in [
        "COMPRA",
        "BUY",
    ]:

        if current_price >= trade.target:

            return {
                "closed": True,
                "result": "WIN",
                "profit_points": (
                    current_price - trade.entry
                ),
            }


        if current_price <= trade.stop:

            return {
                "closed": True,
                "result": "LOSS",
                "profit_points": (
                    current_price - trade.entry
                ),
            }


    # VENDA
    if direction in [
        "VENDA",
        "SELL",
    ]:

        if current_price <= trade.target:

            return {
                "closed": True,
                "result": "WIN",
                "profit_points": (
                    trade.entry - current_price
                ),
            }


        if current_price >= trade.stop:

            return {
                "closed": True,
                "result": "LOSS",
                "profit_points": (
                    trade.entry - current_price
                ),
            }


    return {
        "closed": False,
        "result": None,
        "profit_points": 0,
    }



# =====================================================
# PROCESS OPEN TRADES
# =====================================================


def monitor_open_trades(
    db: Session,
    prices: Dict[str, float],
):
    """
    Monitora operações abertas e fecha quando
    alvo ou stop forem atingidos.
    """

    trades = (
        db.query(AISignalMemory)
        .filter(
            AISignalMemory.result.is_(None)
        )
        .all()
    )


    updated = []


    for trade in trades:

        current_price = prices.get(
            trade.asset
        )


        if current_price is None:
            continue


        result = check_trade_target_stop(
            trade,
            current_price,
        )


        if result["closed"]:

            updated_trade = close_trade_memory(
                db,
                trade.id,
                result["result"],
                result["profit_points"],
            )

            updated.append(
                updated_trade
            )


    return updated