import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import PAGBANK_TOKEN
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Payment, User
from app.schemas_payments import CreateCheckoutRequest, CreateCheckoutResponse
from app.services.pagbank_service import create_pagbank_checkout

router = APIRouter(tags=["payments"])

PLAN_DURATIONS = {
    "mensal": 30,
    "trimestral": 90,
    "semestral": 180,
}


@router.post("/payments/pagbank/checkout", response_model=CreateCheckoutResponse)
def create_checkout(
    payload: CreateCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not PAGBANK_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PAGBANK_TOKEN não configurado",
        )

    try:
        checkout_url, reference_id = create_pagbank_checkout(
            db=db,
            user=current_user,
            plan=payload.plan,
            token=PAGBANK_TOKEN,
        )
        return {
            "checkout_url": checkout_url,
            "reference_id": reference_id,
            "provider": "pagbank",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payments/pagbank/webhook")
async def pagbank_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()

    reference_id = payload.get("reference_id")
    external_id = payload.get("id")
    raw_status = payload.get("status", "")
    status_normalized = str(raw_status).lower()

    if not reference_id:
        raise HTTPException(status_code=400, detail="reference_id ausente no webhook")

    payment = db.query(Payment).filter(Payment.reference_id == reference_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")

    payment.external_id = external_id or payment.external_id
    payment.status = status_normalized
    payment.raw_payload = json.dumps(payload, ensure_ascii=False)

    user = db.query(User).filter(User.id == payment.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # ajuste conforme o status real retornado no seu ambiente;
    # aqui tratamos paid/paid-like como sucesso
    paid_like_status = {"paid", "completed", "succeeded", "authorized"}

    if status_normalized in paid_like_status:
        plan = payment.plan
        user.is_active = True
        user.is_blocked = False
        user.plan = plan
        user.plan_status = "active"
        user.access_expires_at = datetime.utcnow() + timedelta(days=PLAN_DURATIONS[plan])

    db.commit()

    return {"ok": True}