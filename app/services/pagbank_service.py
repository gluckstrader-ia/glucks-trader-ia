import os
import uuid
from typing import Any, Dict, List, Optional

import requests


def get_pagbank_base_url() -> str:
    env = os.getenv("PAGBANK_ENV", "sandbox").strip().lower()
    if env == "production":
        return "https://api.pagseguro.com"
    return "https://sandbox.api.pagseguro.com"


def get_pagbank_headers() -> Dict[str, str]:
    token = os.getenv("PAGBANK_TOKEN", "").strip()

    if not token:
        raise ValueError("PAGBANK_TOKEN não configurado")

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def plan_amount_cents(plan: str) -> int:
    normalized = (plan or "").strip().lower()

    if normalized == "mensal":
        return 19700
    if normalized == "trimestral":
        return 49700
    if normalized == "semestral":
        return 89700

    raise ValueError("Plano inválido. Use mensal, trimestral ou semestral.")


def build_checkout_payload(
    *,
    user_name: str,
    user_email: str,
    plan: str,
    reference_id: str,
    backend_base_url: str,
    frontend_base_url: str,
) -> Dict[str, Any]:
    amount = plan_amount_cents(plan)

    payment_notification_url = f"{backend_base_url.rstrip('/')}/api/webhook/pagbank"
    checkout_notification_url = f"{backend_base_url.rstrip('/')}/api/webhook/pagbank"

    return {
        "reference_id": reference_id,
        "customer": {
            "name": user_name[:100],
            "email": user_email[:150],
        },
        "items": [
            {
                "name": f"Plano {plan.capitalize()} - Gluck's Trader IA",
                "quantity": 1,
                "unit_amount": amount,
            }
        ],
        "notification_urls": [checkout_notification_url],
        "payment_notification_urls": [payment_notification_url],
        "payment_methods": [
            {"type": "CREDIT_CARD"},
            {"type": "DEBIT_CARD"},
            {"type": "PIX"},
            {"type": "BOLETO"},
        ],
        "customer_modifiable": True,
        "address_modifiable": False,
    }


def create_pagbank_checkout(
    *,
    user_name: str,
    user_email: str,
    plan: str,
    backend_base_url: str,
    frontend_base_url: str,
) -> Dict[str, Any]:
    reference_id = f"gluck-{plan}-{uuid.uuid4().hex[:16]}"

    payload = build_checkout_payload(
        user_name=user_name,
        user_email=user_email,
        plan=plan,
        reference_id=reference_id,
        backend_base_url=backend_base_url,
        frontend_base_url=frontend_base_url,
    )

    print("PAGBANK PAYLOAD:", payload)

    response = requests.post(
        f"{get_pagbank_base_url()}/checkouts",
        headers=get_pagbank_headers(),
        json=payload,
        timeout=30,
    )

    try:
        data = response.json()
    except Exception:
        data = {"raw_text": response.text}

    print("PAGBANK RESPONSE STATUS:", response.status_code)
    print("PAGBANK RESPONSE BODY:", data)

    if not response.ok:
        raise ValueError(
            f"Erro ao criar checkout PagBank: status={response.status_code} retorno={data}"
        )

    checkout_id: Optional[str] = data.get("id")
    checkout_url: Optional[str] = None

    links: List[Dict[str, Any]] = data.get("links", []) or []
    for link in links:
        if link.get("rel") == "PAY":
            checkout_url = link.get("href")
            break

    if not checkout_id:
        raise ValueError(f"PagBank não retornou id do checkout. Resposta: {data}")

    if not checkout_url:
        raise ValueError(f"PagBank não retornou links[rel=PAY]. Resposta: {data}")

    return {
        "provider": "pagbank",
        "plan": plan,
        "reference_id": reference_id,
        "external_id": checkout_id,
        "checkout_url": checkout_url,
        "amount": plan_amount_cents(plan),
        "raw_payload": data,
    }