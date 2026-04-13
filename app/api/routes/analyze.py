from typing import Any, Dict, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import get_current_active_user
from app.models import User
from app.services.analysis_service import analyze_asset

from app.database import SessionLocal
from app.services.analysis_history_service import save_analysis

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
    timeframe: Literal["1m", "5m", "15m", "30m", "1h", "4h", "1d"]


@router.post("/analyze", response_model=Dict[str, Any])
async def analyze(
    payload: AnalyzeRequest,
    current_user: User = Depends(get_current_active_user),
):
    try:
        asset_type_normalized = payload.asset_type

        if asset_type_normalized == "indices":
            asset_type_normalized = "index"
        elif asset_type_normalized in {"acoes", "acao"}:
            asset_type_normalized = "stock"
        elif asset_type_normalized in {"acao_br", "acoes_br", "stock_br"}:
            asset_type_normalized = "b3"
        elif asset_type_normalized == "future_br":
            asset_type_normalized = "future_br"
        elif asset_type_normalized in {"future_us", "futuro_us", "futuros_us"}:
            asset_type_normalized = "future_us"
        elif asset_type_normalized in {"commodity", "commodities"}:
            asset_type_normalized = "commodity"

        result = analyze_asset(
            asset=payload.asset,
            asset_type=asset_type_normalized,
            timeframe=payload.timeframe,
        )

        # 🔥 SALVAR NO BANCO
        db = SessionLocal()
        try:
            save_analysis(db, result)
        finally:
            db.close()

        return result

    except ValueError as e:
        print(f"ERRO DE VALIDAÇÃO NO /api/analyze: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        print(f"ERRO NO /api/analyze: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao gerar análise: {str(e)}")