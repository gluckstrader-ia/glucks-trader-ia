from typing import Any, Dict, List, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_current_active_user
from app.models import User
from app.services.radar_service import scan_crypto_market

router = APIRouter(tags=["radar"])


@router.get("/scan/crypto", response_model=List[Dict[str, Any]])
async def scan_crypto(
    timeframe: Literal["1m", "5m", "15m", "30m", "1h", "4h", "1d"] = Query("5m"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return scan_crypto_market(timeframe=timeframe, limit=limit)
    except Exception as e:
        print(f"ERRO NO /api/scan/crypto: {e}")
        raise HTTPException(status_code=500, detail=str(e))