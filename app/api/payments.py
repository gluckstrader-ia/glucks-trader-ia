import uuid
import requests

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Payment, User
from app.core.config import (
    PAGBANK_TOKEN,
    PAGBANK_ENV,
    PAGBANK_NOTIFICATION_URL,
    PAGBANK_REDIRECT_URL,
)
from app.api.auth import get_current_user


router = APIRouter(prefix="/payments", tags=["payments"])


PLANS = {
    "monthly": {"label": "Mensal", "amount": 197.0, "days": 30},
    "quarterly": {"label": "Trimestral", "amount": 497.0, "days": 90},
    "semiannual": {"label": "Semestral", "amount": 897.0, "days": 180},
}


class CheckoutRequest(BaseModel):
    plan: str


@router.post("/create-checkout")
def create_checkout(
    payload: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = payload.plan

    if plan not in PLANS:
        raise HTTPException(status_code=400, detail="Plano inválido")

    if not PAGBANK_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="Token do PagBank não configurado no backend",
        )

    plan_data = PLANS[plan]
    reference_id = str(uuid.uuid4())

    payment = Payment(
        user_id=current_user.id,
        plan=plan,
        amount=plan_data["amount"],
        status="pending",
        pagbank_reference_id=reference_id,
        partner_code=getattr(current_user, "referred_by_code", None),
        partner_user_id=getattr(current_user, "referred_by_user_id", None),
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    pagbank_base_url = (
        "https://sandbox.api.pagseguro.com"
        if PAGBANK_ENV == "sandbox"
        else "https://api.pagseguro.com"
    )

    url = f"{pagbank_base_url}/checkouts"

    headers = {
        "Authorization": f"Bearer {PAGBANK_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload_pagbank = {
        "reference_id": reference_id,
        "customer": {
            "name": current_user.name,
            "email": current_user.email,
        },
        "items": [
            {
                "reference_id": plan,
                "name": f"Gluck's Trader IA - Plano {plan_data['label']}",
                "quantity": 1,
                "unit_amount": int(plan_data["amount"] * 100),
            }
        ],
    }

    if PAGBANK_REDIRECT_URL:
        payload_pagbank["redirect_url"] = PAGBANK_REDIRECT_URL

    if PAGBANK_NOTIFICATION_URL:
        payload_pagbank["notification_urls"] = [PAGBANK_NOTIFICATION_URL]

    try:
        response = requests.post(
            url,
            json=payload_pagbank,
            headers=headers,
            timeout=30,
        )
    except requests.RequestException as exc:
        payment.status = "error"
        db.commit()

        print("Erro de conexão com PagBank:", str(exc))
        raise HTTPException(
            status_code=500,
            detail="Erro de conexão com o PagBank",
        )

    if response.status_code not in [200, 201]:
        payment.status = "error"
        db.commit()

        print("Erro PagBank status:", response.status_code)
        print("Erro PagBank resposta:", response.text)
        print("Payload enviado:", payload_pagbank)

        raise HTTPException(
            status_code=400,
            detail="Erro ao criar pagamento no PagBank",
        )

    data = response.json()

    payment.pagbank_checkout_id = data.get("id")

    pay_url = None
    for link in data.get("links", []):
        if link.get("rel") == "PAY":
            pay_url = link.get("href")
            break

    if not pay_url:
        payment.status = "error"
        db.commit()

        print("PagBank não retornou link PAY:", data)

        raise HTTPException(
            status_code=400,
            detail="PagBank não retornou link de pagamento",
        )

    payment.pagbank_payment_url = pay_url
    db.commit()

    return {
        "success": True,
        "payment_id": payment.id,
        "reference_id": reference_id,
        "plan": plan,
        "amount": plan_data["amount"],
        "checkout_url": pay_url,
    }