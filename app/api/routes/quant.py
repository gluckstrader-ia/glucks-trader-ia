from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import get_current_active_user
from app.models import User
from app.schemas.quant import QuantDashboardResponse
from app.services.quant_service import build_quant_dashboard

router = APIRouter(tags=["quant"])


class QuantRequest(BaseModel):
    asset: str
    asset_type: Literal[
        "index",
        "stock",
        "forex",
        "crypto",
        "b3",
        "commodity",
        "future_br",
        "future_us",
    ]
    timeframe: str


@router.post("/quant/live", response_model=QuantDashboardResponse)
def quant_live(
    payload: QuantRequest,
    current_user: User = Depends(get_current_active_user),
):
    try:
        return build_quant_dashboard(
            asset=payload.asset,
            asset_type=payload.asset_type,
            timeframe=payload.timeframe,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc