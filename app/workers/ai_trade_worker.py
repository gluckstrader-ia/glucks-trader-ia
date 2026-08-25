import time
import traceback

from app.database import SessionLocal

from app.models import AISignalMemory

from app.services.market_data_service import (
    get_current_price,
)

from app.services.ai_trade_monitor_service import (
    check_trade_target_stop,
)

from app.services.ai_trade_outcome_service import (
    close_trade_memory,
)


CHECK_INTERVAL_SECONDS = 30



def run_trade_worker():

    print(
        "AI Trade Worker iniciado"
    )


    while True:

        db = SessionLocal()


        try:

            trades = (
                db.query(AISignalMemory)
                .filter(
                    AISignalMemory.result.is_(None)
                )
                .all()
            )


            for trade in trades:


                try:

                    current_price = get_current_price(
                        asset=trade.asset,
                        asset_type=trade.asset_type,
                        timeframe=trade.timeframe,
                    )


                    result = check_trade_target_stop(
                        trade,
                        current_price,
                    )


                    if result["closed"]:

                        close_trade_memory(
                            db,
                            trade.id,
                            result["result"],
                            result["profit_points"],
                        )


                        print(
                            f"Trade fechado: {trade.asset} - {result['result']}"
                        )


                except Exception as error:

                    print(
                        f"Erro monitorando {trade.asset}: {error}"
                    )



        except Exception as error:

            print(
                "Erro no AI Trade Worker:",
                error,
            )

            traceback.print_exc()


        finally:

            db.close()


        time.sleep(
            CHECK_INTERVAL_SECONDS
        )



if __name__ == "__main__":

    run_trade_worker()