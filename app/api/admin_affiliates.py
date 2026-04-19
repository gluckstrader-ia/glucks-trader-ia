from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin_user
from app.models import User
from app.models_affiliate import AffiliateCommission

router = APIRouter(prefix="/admin/affiliates", tags=["admin-affiliates"])


@router.get("/overview")
def affiliates_overview(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    total_partners = db.query(func.count(User.id)).filter(
        User.is_partner == True
    ).scalar() or 0

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
    commission = db.query(AffiliateCommission).filter(
        AffiliateCommission.id == commission_id
    ).first()

    if not commission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comissão não encontrada",
        )

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