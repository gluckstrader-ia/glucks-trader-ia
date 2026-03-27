import json
import uuid
from typing import Tuple

import requests
from sqlalchemy.orm import Session

from app.core.config import (
    FRONTEND_SUCCESS_URL,
    PAGBANK_ENV,
    PAGBANK_NOTIFICATION_URL,
)
from app.models import Payment, User

PLAN_CATALOG = {
    "mensal": {"amount": 19700, "name": "Plano Mensal Gluck's Trader IA"},
    "trimestral": {"amount": 49700, "name": "Plano Trimestral Gluck's Trader IA"},
    "semestral": {"amount": 89700, "name": "Plano Semestral Gluck's Trader IA"},
}


def get_pagbank_base_url() -> str:
    if PAGBANK_ENV.lower() == "production":
        return "https://api.pagseguro.com"
    return "https://sandbox.api.pagseguro.com"


def build_reference_id(user_id: int, plan: str) -> str:
    return f"user_{user_id}_{plan}_{uuid.uuid4().hex[:12]}"


def create_pagbank_checkout(db: Session, user: User, plan: str, token: str) -> Tuple[str, str]:
    if plan not in PLAN_CATALOG:
        raise ValueError("Plano inválido")

    item = PLAN_CATALOG[plan]
    reference_id = build_reference_id(user.id, plan)

    payload = {
        "reference_id": reference_id,
        "expiration_date": "2026-12-31T23:59:59-03:00",
        "customer": {
            "name": user.name,
            "email": user.email,
            # se você ainda não coleta CPF/telefone no cadastro, deixe o checkout hospedado pedir isso
        },
        "customer_modifiable": True,
        "items": [
            {
                "name": item["name"],
                "quantity": 1,
                "unit_amount": item["amount"],
            }
        ],
        "payment_methods": [
            {"type": "PIX"},
            {"type": "CREDIT_CARD"},
        ],
        "redirect_url": FRONTEND_SUCCESS_URL,
        "notification_urls": [PAGBANK_NOTIFICATION_URL],
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    response = requests.post(
        f"{get_pagbank_base_url()}/checkouts",
        headers=headers,
        json=payload,
        timeout=30,
    )

    if not response.ok:
        raise Exception(f"Erro PagBank: {response.status_code} - {response.text}")

    data = response.json()

    pay_link = None
    for link in data.get("links", []):
        if link.get("rel") == "PAY":
            pay_link = link.get("href")
            break

    if not pay_link:
        raise Exception("PagBank não retornou link de pagamento")

    payment = Payment(
        user_id=user.id,
        provider="pagbank",
        plan=plan,
        reference_id=reference_id,
        external_id=data.get("id"),
        checkout_url=pay_link,
        status=data.get("status", "pending").lower(),
        amount=item["amount"],
        raw_payload=json.dumps(data, ensure_ascii=False),
    )
    db.add(payment)

    user.pagbank_reference = reference_id

    db.commit()
    db.refresh(payment)

    return pay_link, reference_id