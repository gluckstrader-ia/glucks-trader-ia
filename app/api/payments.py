from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user
from app.services.pagbank_service import create_pagbank_checkout

router = APIRouter(prefix="/api/payments", tags=["payments"])

PLAN_PRICES = {
    "mensal": 19700,
    "trimestral": 49700,
    "semestral": 89700,
}

@router.post("/create-checkout")
async def create_checkout(data: dict, current_user=Depends(get_current_user)):
    plan = data.get("plan")

    if plan not in PLAN_PRICES:
        raise HTTPException(status_code=400, detail="Plano inválido")

    checkout = await create_pagbank_checkout(
        user_email=current_user.email,
        plan_name=plan,
        amount_cents=PLAN_PRICES[plan],
    )

    pay_url = None

    for link in checkout.get("links", []):
        if link.get("rel") == "PAY":
            pay_url = link.get("href")
            break

    if not pay_url:
        raise HTTPException(
            status_code=500,
            detail=f"Checkout criado sem link PAY. Resposta: {checkout}"
        )

    return {
        "checkout_id": checkout.get("id"),
        "pay_url": pay_url,
    }
