from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import hash_password, generate_partner_code
from app.database import get_db
from app.dependencies import get_current_admin_user
from app.models import User
from app.models_affiliate import AffiliateCommission

router = APIRouter(prefix="/admin/affiliates", tags=["admin-affiliates"])


class CreateAffiliateRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    partner_code: Optional[str] = None
    partner_pix_key: Optional[str] = None
    partner_pix_type: Optional[str] = None


class CreateManualCommissionRequest(BaseModel):
    partner_code: str
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_user_id: Optional[int] = None
    plan: Optional[str] = "mensal"
    gross_amount: float
    commission_percent: float = 10.0
    status: str = "pending"
    billing_cycle: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None


def normalize_code(code: str) -> str:
    return (
        str(code or "")
        .strip()
        .upper()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )


@router.post("/create")
def create_affiliate(
    payload: CreateAffiliateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    email = payload.email.lower().strip()

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    if payload.partner_code:
        partner_code = normalize_code(payload.partner_code)
    else:
        partner_code = generate_partner_code(db, payload.name)

    code_exists = db.query(User).filter(User.partner_code == partner_code).first()
    if code_exists:
        raise HTTPException(status_code=400, detail="Código de afiliado já existe")

    user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        is_active=True,
        is_blocked=False,
        is_admin=False,
        is_partner=True,
        partner_code=partner_code,
        partner_status="active",
        partner_pix_key=payload.partner_pix_key,
        partner_pix_type=payload.partner_pix_type,
        plan="partner",
        plan_status="active",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Afiliado criado com sucesso",
        "partner": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "partner_code": user.partner_code,
            "partner_status": user.partner_status,
        },
    }


@router.get("/overview")
def affiliates_overview(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    total_partners = db.query(func.count(User.id)).filter(User.is_partner == True).scalar() or 0

    pending_amount = db.query(func.coalesce(func.sum(AffiliateCommission.commission_amount), 0)).filter(
        AffiliateCommission.status == "pending"
    ).scalar() or 0

    available_amount = db.query(func.coalesce(func.sum(AffiliateCommission.commission_amount), 0)).filter(
        AffiliateCommission.status == "available"
    ).scalar() or 0

    paid_amount = db.query(func.coalesce(func.sum(AffiliateCommission.commission_amount), 0)).filter(
        AffiliateCommission.status == "paid"
    ).scalar() or 0

    total_commissions = db.query(func.count(AffiliateCommission.id)).scalar() or 0

    return {
        "total_partners": total_partners,
        "total_commissions": total_commissions,
        "pending_amount": round(float(pending_amount), 2),
        "available_amount": round(float(available_amount), 2),
        "paid_amount": round(float(paid_amount), 2),
    }


@router.get("/partners")
def list_partners(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    partners = db.query(User).filter(User.is_partner == True).order_by(User.created_at.desc()).all()

    return {
        "items": [
            {
                "id": p.id,
                "name": p.name,
                "email": p.email,
                "partner_code": p.partner_code,
                "partner_status": getattr(p, "partner_status", "active"),
                "partner_pix_key": getattr(p, "partner_pix_key", None),
                "partner_pix_type": getattr(p, "partner_pix_type", None),
                "is_active": p.is_active,
                "is_blocked": p.is_blocked,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in partners
        ]
    }


@router.post("/commissions/manual")
def create_manual_commission(
    payload: CreateManualCommissionRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    partner_code = normalize_code(payload.partner_code)

    partner = db.query(User).filter(
        User.partner_code == partner_code,
        User.is_partner == True,
    ).first()

    if not partner:
        raise HTTPException(status_code=404, detail="Afiliado não encontrado")

    commission_amount = round(float(payload.gross_amount) * float(payload.commission_percent) / 100, 2)

    commission = AffiliateCommission(
        partner_user_id=partner.id,
        customer_user_id=payload.customer_user_id,
        customer_name=payload.customer_name,
        customer_email=str(payload.customer_email) if payload.customer_email else None,
        plan=payload.plan,
        gross_amount=round(float(payload.gross_amount), 2),
        commission_percent=payload.commission_percent,
        commission_amount=commission_amount,
        status=payload.status,
        billing_cycle=payload.billing_cycle,
        payment_reference=payload.payment_reference,
        notes=payload.notes,
    )

    db.add(commission)
    db.commit()
    db.refresh(commission)

    return {
        "message": "Comissão lançada com sucesso",
        "commission": {
            "id": commission.id,
            "partner_code": partner.partner_code,
            "partner_name": partner.name,
            "gross_amount": commission.gross_amount,
            "commission_amount": commission.commission_amount,
            "status": commission.status,
        },
    }


@router.get("/commissions")
def list_affiliate_commissions(
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    query = db.query(AffiliateCommission)

    if status_filter:
        query = query.filter(AffiliateCommission.status == status_filter)

    commissions = query.order_by(AffiliateCommission.created_at.desc()).limit(200).all()

    items = []
    for c in commissions:
        partner = db.query(User).filter(User.id == c.partner_user_id).first()

        items.append(
            {
                "id": c.id,
                "partner_user_id": c.partner_user_id,
                "partner_name": partner.name if partner else None,
                "partner_email": partner.email if partner else None,
                "partner_code": partner.partner_code if partner else None,
                "customer_user_id": c.customer_user_id,
                "customer_name": getattr(c, "customer_name", None),
                "customer_email": getattr(c, "customer_email", None),
                "plan": c.plan,
                "gross_amount": c.gross_amount,
                "commission_percent": c.commission_percent,
                "commission_amount": c.commission_amount,
                "status": c.status,
                "billing_cycle": c.billing_cycle,
                "payment_reference": c.payment_reference,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "available_at": c.available_at.isoformat() if c.available_at else None,
                "paid_at": c.paid_at.isoformat() if c.paid_at else None,
            }
        )

    return {"items": items}


@router.post("/commissions/{commission_id}/mark-paid")
def mark_commission_paid(
    commission_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    commission = db.query(AffiliateCommission).filter(AffiliateCommission.id == commission_id).first()

    if not commission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comissão não encontrada")

    if commission.status == "paid":
        return {"message": "Comissão já estava marcada como paga."}

    commission.status = "paid"
    commission.paid_at = datetime.utcnow()

    db.add(commission)
    db.commit()
    db.refresh(commission)

    return {
        "message": "Comissão marcada como paga com sucesso.",
        "commission_id": commission.id,
        "status": commission.status,
        "paid_at": commission.paid_at.isoformat() if commission.paid_at else None,
    }