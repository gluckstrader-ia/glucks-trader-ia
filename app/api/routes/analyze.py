from typing import Any, Dict, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import SessionLocal
from app.dependencies import get_current_active_user
from app.models import User
from app.services.analysis_history_service import save_analysis
from app.services.analysis_service import analyze_asset
from app.services.ai_brain_service import build_ai_brain


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
    "/analyze",
    response_model=Dict[str, Any],
)
async def analyze(
    payload: AnalyzeRequest,
    current_user: User = Depends(
        get_current_active_user
    ),
):
    """
    Endpoint principal de análise de mercado.

    Fluxo:

    1. Normaliza o tipo de ativo.
    2. Executa o motor de análise existente.
    3. Executa o AI Brain sobre o resultado.
    4. Adiciona a interpretação ao payload.
    5. Salva a análise no histórico.
    6. Retorna o resultado completo ao frontend.

    O AI Brain não altera:
    - direção original;
    - entrada;
    - stop;
    - alvos;
    - probabilidade do motor existente.
    """

    try:
        asset_type_normalized = payload.asset_type

        # ==========================================
        # NORMALIZAÇÃO DOS TIPOS DE ATIVO
        # ==========================================

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

        elif asset_type_normalized == "future_br":
            asset_type_normalized = "future_br"

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

        # ==========================================
        # MOTOR PRINCIPAL DE ANÁLISE
        # ==========================================

        result = analyze_asset(
            asset=payload.asset,
            asset_type=asset_type_normalized,
            timeframe=payload.timeframe,
        )

        # ==========================================
        # AI BRAIN
        # ==========================================
        #
        # O AI Brain interpreta o resultado pronto.
        #
        # Ele NÃO altera o sinal original.
        # Ele apenas adiciona:
        #
        # - score de qualidade;
        # - confiança interpretada;
        # - classificação;
        # - motivos;
        # - alertas.
        #

        ai_brain = build_ai_brain(result)

        result["ai_brain"] = ai_brain

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

        # ==========================================
        # RESPOSTA PARA O FRONTEND
        # ==========================================

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