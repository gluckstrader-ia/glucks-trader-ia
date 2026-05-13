from typing import Optional, Literal
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CommunityMessage, User
from app.api.auth import get_current_user

router = APIRouter(prefix="/community", tags=["community"])


class CommunityMessageCreate(BaseModel):
    channel: Literal["Geral", "Avisos", "Forex", "B3", "Dúvidas"]
    message_type: Literal["text", "image", "video"] = "text"
    content: Optional[str] = None
    media_url: Optional[str] = None


class CommunityMessageResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    channel: str
    message_type: str
    content: Optional[str]
    media_url: Optional[str]
    created_at: Optional[str]

    class Config:
        from_attributes = True


@router.get("/messages")
def list_messages(
    channel: str = "Geral",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    allowed_channels = ["Geral", "Avisos", "Forex", "B3", "Dúvidas"]

    if channel not in allowed_channels:
        raise HTTPException(status_code=400, detail="Canal inválido")

    messages = (
        db.query(CommunityMessage)
        .filter(CommunityMessage.channel == channel)
        .order_by(CommunityMessage.created_at.desc())
        .limit(50)
        .all()
    )

    messages = list(reversed(messages))

    return [
        {
            "id": msg.id,
            "user_id": msg.user_id,
            "user_name": msg.user_name,
            "channel": msg.channel,
            "message_type": msg.message_type,
            "content": msg.content,
            "media_url": msg.media_url,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }
        for msg in messages
    ]


@router.post("/messages")
def create_message(
    payload: CommunityMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = (payload.content or "").strip()
    media_url = (payload.media_url or "").strip()

    if payload.message_type == "text" and not content:
        raise HTTPException(status_code=400, detail="Mensagem vazia")

    if payload.message_type in ["image", "video"] and not content and not media_url:
        raise HTTPException(status_code=400, detail="Informe texto ou link de mídia")

    message = CommunityMessage(
        user_id=current_user.id,
        user_name=current_user.name or current_user.email,
        channel=payload.channel,
        message_type=payload.message_type,
        content=content,
        media_url=media_url or None,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return {
        "id": message.id,
        "user_id": message.user_id,
        "user_name": message.user_name,
        "channel": message.channel,
        "message_type": message.message_type,
        "content": message.content,
        "media_url": message.media_url,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }