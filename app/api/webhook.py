from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Payment, User

router = APIRouter(tags=["webhook"])


def plan_days(plan: str) -> int:
    normalized = (plan or "").strip().lower()

    if normalized == "mensal":
        return 30
    if normalized == "trimestral":
        return 90
    if normalized == "semestral":
        return 180

    return 30


def extract_reference_id(payload: Dict[str, Any]) -> Optional[str]:
    # compatível com variações comuns do payload
    if payload.get("reference_id"):
        return payload.get("reference_id")
    if payload.get("referenceId"):
        return payload.get("referenceId")

    data = payload.get("data") or {}
    if data.get("reference_id"):
        return data.get("reference_id")
    if data.get("referenceId"):
        return data.get("referenceId")

    payment = data.get("payment") or payload.get("payment") or {}
    if payment.get("reference_id"):
        return payment.get("reference_id")
    if payment.get("referenceId"):
        return payment.get("referenceId")

    return None


def extract_status(payload: Dict[str, Any]) -> Optional[str]:
    if payload.get("status"):
        return str(payload.get("status"))

    data = payload.get("data") or {}
    if data.get("status"):
        return str(data.get("status"))

    payment = data.get("payment") or payload.get("payment") or {}
    if payment.get("status"):
        return str(payment.get("status"))

    return None


@router.post("/webhook/pagbank")
async def pagbank_webhook(request: Request):
    db_gen = get_db()
    db: Session = next(db_gen)

    try:
        payload = await request.json()
        print("WEBHOOK PAGBANK RECEBIDO:", payload)

        reference_id = extract_reference_id(payload)
        status = extract_status(payload)

        if not reference_id:
            raise HTTPException(status_code=400, detail="reference_id não encontrado no webhook")

        payment = (
            db.query(Payment)
            .filter(Payment.reference_id == reference_id)
            .first()
        )

        if not payment:
            raise HTTPException(status_code=404, detail="Pagamento não encontrado")

        if status:
            payment.status = status.lower()

        # status transacional documentado inclui PAID, IN_ANALYSIS, DECLINED, CANCELED, WAITING
        if status and str(status).upper() == "PAID":
            user = db.query(User).filter(User.id == payment.user_id).first()

            if user:
                days = plan_days(payment.plan)

                base_date = (
                    user.access_expires_at
                    if user.access_expires_at and user.access_expires_at > datetime.utcnow()
                    else datetime.utcnow()
                )

                user.is_active = True
                user.is_blocked = False
                user.plan = (payment.plan or "mensal").strip().lower()
                user.plan_status = "active"
                user.access_expires_at = base_date + timedelta(days=days)

                db.add(user)

        db.add(payment)
        db.commit()

        return {"message": "Webhook processado com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        print("ERRO WEBHOOK PAGBANK:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
        try:
            next(db_gen)
        except StopIteration:
            pass