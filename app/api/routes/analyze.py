from typing import Any, Dict, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import SessionLocal
from app.dependencies import get_current_active_user
from app.models import User
from app.services.analysis_history_service import save_analysis
from app.services.analysis_service import analyze_asset
from app.services.ai_brain_service import build_ai_brain
from app.services.ai_memory_service import (
    store_signal_memory,
    analyze_memory_context,
)
from app.services.ai_memory_database_service import save_ai_memory
from app.services.ai_memory_context_service import build_memory_context


router = APIRouter(tags=["analyze"])


class AnalyzeRequest(BaseModel):

    asset: str

    asset_type: Literal[
        "crypto",
        "forex",
        "stock",
        "index",
        "indices",
        "acoes",
        "acao",
        "b3",
        "acao_br",
        "acoes_br",
        "stock_br",
        "future_br",
        "future_us",
        "futuro_us",
        "futuros_us",
        "commodity",
        "commodities",
    ]

    timeframe: Literal[
        "1m",
        "5m",
        "15m",
        "30m",
        "1h",
        "4h",
        "1d",
    ]


@router.post(
    "/analyze/live",
    response_model=Dict[str, Any],
)
async def analyze_live(
    payload: AnalyzeRequest,
    current_user: User = Depends(
        get_current_active_user
    ),
):
    """
    Reprocessamento leve usado exclusivamente pelo Painel Técnico Vivo.

    IMPORTANTE:
    - calcula mercado + AI Brain com dados atuais;
    - NÃO grava histórico de análises;
    - NÃO grava memória de sinais;
    - NÃO altera os outros painéis do frontend.

    O frontend chama esta rota somente depois da primeira análise manual.
    """

    try:
        asset_type_normalized = payload.asset_type

        if asset_type_normalized == "indices":
            asset_type_normalized = "index"

        elif asset_type_normalized in {
            "acoes",
            "acao",
        }:
            asset_type_normalized = "stock"

        elif asset_type_normalized in {
            "acao_br",
            "acoes_br",
            "stock_br",
        }:
            asset_type_normalized = "b3"

        elif asset_type_normalized in {
            "future_us",
            "futuro_us",
            "futuros_us",
        }:
            asset_type_normalized = "future_us"

        elif asset_type_normalized in {
            "commodity",
            "commodities",
        }:
            asset_type_normalized = "commodity"

        result = analyze_asset(
            asset=payload.asset,
            asset_type=asset_type_normalized,
            timeframe=payload.timeframe,
        )

        # O motor vivo precisa da mesma decisão estratégica usada no painel,
        # mas sem persistir a leitura em histórico/memória a cada atualização.
        result["ai_brain"] = build_ai_brain(result)

        return result

    except ValueError as e:
        print(
            f"ERRO DE VALIDAÇÃO NO /api/analyze/live: {e}"
        )

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:
        print(
            f"ERRO NO /api/analyze/live: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Erro interno ao atualizar o painel vivo: "
                f"{str(e)}"
            ),
        )


@router.post(
    "/analyze",
    response_model=Dict[str, Any],
)
async def analyze(
    payload: AnalyzeRequest,
    current_user: User = Depends(
        get_current_active_user
    ),
):

    try:

        asset_type_normalized = payload.asset_type


        if asset_type_normalized == "indices":
            asset_type_normalized = "index"

        elif asset_type_normalized in {
            "acoes",
            "acao",
        }:
            asset_type_normalized = "stock"

        elif asset_type_normalized in {
            "acao_br",
            "acoes_br",
            "stock_br",
        }:
            asset_type_normalized = "b3"

        elif asset_type_normalized in {
            "future_us",
            "futuro_us",
            "futuros_us",
        }:
            asset_type_normalized = "future_us"

        elif asset_type_normalized in {
            "commodity",
            "commodities",
        }:
            asset_type_normalized = "commodity"


        result = analyze_asset(
            asset=payload.asset,
            asset_type=asset_type_normalized,
            timeframe=payload.timeframe,
        )


        # ==========================================
        # AI BRAIN
        # ==========================================

        ai_brain = build_ai_brain(
            result
        )

        result["ai_brain"] = ai_brain

        # ==========================================
        # AI MEMORY CONTEXT
        # ==========================================

        db = SessionLocal()

        try:

            memory_context = build_memory_context(
                db,
                result,
            )

            result["memory_context"] = memory_context

        finally:

            db.close()


        # ==========================================
        # AI MEMORY CONTEXT V1.1
        # ==========================================
        #
        # Consulta histórico.
        # Não altera sinal ou decisão.
        #

        memory_context = analyze_memory_context(
            asset=result.get(
                "asset",
                payload.asset,
            ),

            timeframe=result.get(
                "timeframe",
                payload.timeframe,
            ),

            direction=result.get(
                "final_signal",
                {},
            ).get(
                "direction",
                "NEUTRO",
            ),

            module_alignment=ai_brain.get(
                "module_alignment",
                "NEUTRO",
            ),
        )


        result["memory_context"] = memory_context


        # ==========================================
        # AI MEMORY STORAGE
        # ==========================================

        store_signal_memory(
            result
        )

        # ==========================================
        # AI MEMORY DATABASE V2
        # ==========================================

        db = SessionLocal()

        try:

            save_ai_memory(
                db,
                result,
            )

        finally:

            db.close()

        # ==========================================
        # HISTÓRICO
        # ==========================================

        db = SessionLocal()

        try:

            save_analysis(
                db,
                result,
            )

        finally:

            db.close()


        return result


    except ValueError as e:

        print(
            f"ERRO DE VALIDAÇÃO NO /api/analyze: {e}"
        )

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


    except Exception as e:

        print(
            f"ERRO NO /api/analyze: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Erro interno ao gerar análise: "
                f"{str(e)}"
            ),
        )