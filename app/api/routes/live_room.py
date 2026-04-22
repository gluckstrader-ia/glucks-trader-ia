from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel

from app.dependencies import get_current_active_user
from app.models import User
from app.services.live_room.engine import analyze_live_room_asset
from app.services.live_room.schemas import LiveRoomResponse
from app.services.live_room.voice_engine import synthesize_live_room_voice

router = APIRouter(prefix="/live-room", tags=["live-room"])


class LiveRoomVoiceRequest(BaseModel):
    text: str


@router.get("/analyze", response_model=LiveRoomResponse)
def analyze_live_room(
    asset: str = Query(..., description="Ativo para a Sala ao Vivo IA"),
    timeframe: str = Query("5m", description="Timeframe da análise"),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return analyze_live_room_asset(asset=asset, timeframe=timeframe)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        print("ERRO /live-room/voice:", repr(exc))
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar voz premium: {str(exc)}",
        ) from exc


@router.post("/voice")
def generate_live_room_voice(
    payload: LiveRoomVoiceRequest,
    current_user: User = Depends(get_current_active_user),
):
    try:
        audio_bytes = synthesize_live_room_voice(payload.text)
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Cache-Control": "no-store",
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar voz premium: {str(exc)}",
        ) from exc