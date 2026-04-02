import json
import os
from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Payment, User
from app.services.pagbank_service import create_pagbank_checkout

router = APIRouter(tags=["payments"])


class CreateCheckoutRequest(BaseModel):
    plan: Literal["mensal", "trimestral", "semestral"]


class CreateCheckoutResponse(BaseModel):
    message: str
    checkout_url: str
    payment_id: int
    reference_id: str
    external_id: Optional[str] = None
    plan: str
    amount: int


@router.post("/payments/create-checkout", response_model=CreateCheckoutResponse)
def create_checkout(
    payload: CreateCheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        backend_base_url = os.getenv("BACKEND_BASE_URL", "").strip()
        frontend_base_url = os.getenv("FRONTEND_BASE_URL", "").strip()

        if not backend_base_url:
            raise ValueError("BACKEND_BASE_URL não configurado")
        if not frontend_base_url:
            raise ValueError("FRONTEND_BASE_URL não configurado")

        checkout = create_pagbank_checkout(
            user_name=current_user.name,
            user_email=current_user.email,
            plan=payload.plan,
            backend_base_url=backend_base_url,
            frontend_base_url=frontend_base_url,
        )

        payment = Payment(
            user_id=current_user.id,
            provider=checkout["provider"],
            plan=checkout["plan"],
            reference_id=checkout["reference_id"],
            external_id=checkout["external_id"],
            checkout_url=checkout["checkout_url"],
            status="pending",
            amount=checkout["amount"],
            raw_payload=json.dumps(checkout["raw_payload"], ensure_ascii=False),
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        return CreateCheckoutResponse(
            message="Checkout criado com sucesso",
            checkout_url=payment.checkout_url or "",
            payment_id=payment.id,
            reference_id=payment.reference_id,
            external_id=payment.external_id,
            plan=payment.plan,
            amount=payment.amount,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao criar checkout: {str(e)}",
        )