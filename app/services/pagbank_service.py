import os
import httpx

PAGBANK_API_URL = os.getenv("PAGBANK_API_URL", "").rstrip("/")
PAGBANK_TOKEN = os.getenv("PAGBANK_TOKEN")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "").rstrip("/")

async def create_pagbank_checkout(user_email: str, plan_name: str, amount_cents: int):
    url = f"{PAGBANK_API_URL}/checkouts"

    redirect_url = f"{FRONTEND_BASE_URL}/premium"

    payload = {
        "reference_id": f"{user_email}-{plan_name}",
        "return_url": return_url,
        "items": [
            {
                "reference_id": plan_name.lower(),
                "name": plan_name,
                "quantity": 1,
                "unit_amount": amount_cents
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {PAGBANK_TOKEN}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()