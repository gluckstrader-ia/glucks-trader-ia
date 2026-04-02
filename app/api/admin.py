from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin_user
from app.models import Payment, User

router = APIRouter(tags=["admin"])


class AdminUserUpdateRequest(BaseModel):
    user_id: int
    name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    is_blocked: Optional[bool] = None
    is_admin: Optional[bool] = None
    plan: Optional[str] = None
    plan_status: Optional[str] = None
    access_expires_at: Optional[datetime] = None


class AdminConfirmPaymentRequest(BaseModel):
    payment_id: int
    activate_user: bool = True


def _plan_days(plan: str) -> int:
    normalized = (plan or "").strip().lower()

    if normalized == "mensal":
        return 30
    if normalized == "trimestral":
        return 90
    if normalized == "semestral":
        return 180

    return 30


@router.get("/admin/users", response_model=List[Dict[str, Any]])
def list_users(
    search: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    query = db.query(User)

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            (User.name.ilike(term)) | (User.email.ilike(term))
        )

    users = query.order_by(User.created_at.desc()).all()

    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_active": user.is_active,
            "is_blocked": user.is_blocked,
            "is_admin": user.is_admin,
            "plan": user.plan,
            "plan_status": user.plan_status,
            "access_expires_at": user.access_expires_at.isoformat() if user.access_expires_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }
        for user in users
    ]


@router.get("/admin/users/{user_id}", response_model=Dict[str, Any])
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "is_active": user.is_active,
        "is_blocked": user.is_blocked,
        "is_admin": user.is_admin,
        "plan": user.plan,
        "plan_status": user.plan_status,
        "access_expires_at": user.access_expires_at.isoformat() if user.access_expires_at else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


@router.put("/admin/users/{user_id}", response_model=Dict[str, Any])
def update_user(
    user_id: int,
    payload: AdminUserUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if payload.user_id != user_id:
        raise HTTPException(status_code=400, detail="ID do payload diferente do ID da rota")

    if payload.name is not None:
        user.name = payload.name.strip()

    if payload.email is not None:
        normalized_email = payload.email.strip().lower()

        existing = (
            db.query(User)
            .filter(User.email == normalized_email, User.id != user_id)
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="E-mail já está em uso por outro usuário")

        user.email = normalized_email

    if payload.is_active is not None:
        user.is_active = payload.is_active

    if payload.is_blocked is not None:
        user.is_blocked = payload.is_blocked

    if payload.is_admin is not None:
        user.is_admin = payload.is_admin

    if payload.plan is not None:
        user.plan = payload.plan.strip().lower()

    if payload.plan_status is not None:
        user.plan_status = payload.plan_status.strip().lower()

    if payload.access_expires_at is not None:
        user.access_expires_at = payload.access_expires_at

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Usuário atualizado com sucesso",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_active": user.is_active,
            "is_blocked": user.is_blocked,
            "is_admin": user.is_admin,
            "plan": user.plan,
            "plan_status": user.plan_status,
            "access_expires_at": user.access_expires_at.isoformat() if user.access_expires_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        },
    }


@router.post("/admin/users/{user_id}/toggle-block", response_model=Dict[str, Any])
def toggle_block_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.is_blocked = not user.is_blocked
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Status de bloqueio atualizado com sucesso",
        "user_id": user.id,
        "is_blocked": user.is_blocked,
    }


@router.post("/admin/users/{user_id}/toggle-active", response_model=Dict[str, Any])
def toggle_active_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.is_active = not user.is_active
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Status de ativação atualizado com sucesso",
        "user_id": user.id,
        "is_active": user.is_active,
    }


@router.get("/admin/payments", response_model=List[Dict[str, Any]])
def list_payments(
    search: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    query = db.query(Payment, User).join(User, Payment.user_id == User.id)

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            (User.name.ilike(term))
            | (User.email.ilike(term))
            | (Payment.reference_id.ilike(term))
            | (Payment.external_id.ilike(term))
        )

    if status_filter and status_filter.strip():
        query = query.filter(Payment.status == status_filter.strip().lower())

    rows = query.order_by(Payment.created_at.desc()).all()

    return [
        {
            "id": payment.id,
            "user_id": user.id,
            "user_name": user.name,
            "user_email": user.email,
            "provider": payment.provider,
            "plan": payment.plan,
            "reference_id": payment.reference_id,
            "external_id": payment.external_id,
            "checkout_url": payment.checkout_url,
            "status": payment.status,
            "amount": payment.amount,
            "amount_brl": round(payment.amount / 100, 2),
            "created_at": payment.created_at.isoformat() if payment.created_at else None,
            "updated_at": payment.updated_at.isoformat() if payment.updated_at else None,
        }
        for payment, user in rows
    ]


@router.post("/admin/payments/{payment_id}/confirm", response_model=Dict[str, Any])
def confirm_payment(
    payment_id: int,
    payload: AdminConfirmPaymentRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")

    if payload.payment_id != payment_id:
        raise HTTPException(status_code=400, detail="ID do payload diferente do ID da rota")

    user = db.query(User).filter(User.id == payment.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário do pagamento não encontrado")

    payment.status = "paid"

    if payload.activate_user:
        days = _plan_days(payment.plan)
        base_date = user.access_expires_at if user.access_expires_at and user.access_expires_at > datetime.utcnow() else datetime.utcnow()

        user.is_active = True
        user.is_blocked = False
        user.plan = (payment.plan or "mensal").strip().lower()
        user.plan_status = "active"
        user.access_expires_at = base_date + timedelta(days=days)

        db.add(user)

    db.add(payment)
    db.commit()
    db.refresh(payment)
    db.refresh(user)

    return {
        "message": "Pagamento confirmado e acesso atualizado com sucesso",
        "payment": {
            "id": payment.id,
            "status": payment.status,
            "plan": payment.plan,
            "user_id": payment.user_id,
        },
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_active": user.is_active,
            "plan": user.plan,
            "plan_status": user.plan_status,
            "access_expires_at": user.access_expires_at.isoformat() if user.access_expires_at else None,
        },
    }


@router.post("/admin/payments/{payment_id}/mark-pending", response_model=Dict[str, Any])
def mark_payment_pending(
    payment_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")

    payment.status = "pending"
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {
        "message": "Pagamento marcado como pendente",
        "payment": {
            "id": payment.id,
            "status": payment.status,
        },
    }