from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.models_affiliate import AffiliateClick, AffiliateCommission, AffiliateMaterial
from app.services.affiliate_service import create_partner_if_needed

router = APIRouter(prefix="/partners", tags=["partners"])


@router.post("/join")
def join_partner_program(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = create_partner_if_needed(db, current_user)

    return {
        "message": "Programa de parceiros ativado com sucesso.",
        "partner_code": user.partner_code,
        "partner_status": user.partner_status,
    }


@router.post("/track-click/{partner_code}")
def track_click(partner_code: str, request: Request, db: Session = Depends(get_db)):
    partner = db.query(User).filter(
        User.partner_code == partner_code,
        User.is_partner == True,
        User.partner_status == "active",
    ).first()

    if not partner:
        return {"ok": False, "message": "Código inválido"}

    click = AffiliateClick(
        partner_code=partner_code,
        landing_page=str(request.url),
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    db.add(click)
    db.commit()

    return {"ok": True}


@router.post("/pix")
def save_partner_pix(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_partner:
        raise HTTPException(status_code=403, detail="Usuário não é parceiro.")

    pix_key = (payload.get("pix_key") or "").strip()
    pix_type = (payload.get("pix_type") or "").strip()

    if not pix_key or not pix_type:
        raise HTTPException(status_code=400, detail="Informe chave Pix e tipo.")

    current_user.partner_pix_key = pix_key
    current_user.partner_pix_type = pix_type

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return {"message": "Chave Pix salva com sucesso."}


@router.get("/dashboard")
def get_partner_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_partner:
        raise HTTPException(status_code=403, detail="Usuário não é parceiro.")

    total_clicks = db.query(func.count(AffiliateClick.id)).filter(
        AffiliateClick.partner_code == current_user.partner_code
    ).scalar() or 0

    total_referred_users = db.query(func.count(User.id)).filter(
        User.referred_by_user_id == current_user.id
    ).scalar() or 0

    active_customers = db.query(func.count(User.id)).filter(
        User.referred_by_user_id == current_user.id,
        User.is_active == True
    ).scalar() or 0

    pending_amount = db.query(func.coalesce(func.sum(AffiliateCommission.commission_amount), 0)).filter(
        AffiliateCommission.partner_user_id == current_user.id,
        AffiliateCommission.status == "pending"
    ).scalar() or 0

    available_amount = db.query(func.coalesce(func.sum(AffiliateCommission.commission_amount), 0)).filter(
        AffiliateCommission.partner_user_id == current_user.id,
        AffiliateCommission.status == "available"
    ).scalar() or 0

    paid_amount = db.query(func.coalesce(func.sum(AffiliateCommission.commission_amount), 0)).filter(
        AffiliateCommission.partner_user_id == current_user.id,
        AffiliateCommission.status == "paid"
    ).scalar() or 0

    commissions = db.query(AffiliateCommission).filter(
        AffiliateCommission.partner_user_id == current_user.id
    ).order_by(AffiliateCommission.created_at.desc()).limit(50).all()

    materials = db.query(AffiliateMaterial).filter(
        AffiliateMaterial.is_active == True
    ).order_by(AffiliateMaterial.created_at.desc()).all()

    return {    
        "partner_code": current_user.partner_code,
        "partner_link": f"https://www.gluckstrader.com.br/cadastro?ref={current_user.partner_code}",
        "pix_key": current_user.partner_pix_key,
        "pix_type": current_user.partner_pix_type,
        "metrics": {
            "clicks": total_clicks,
            "referred_users": total_referred_users,
            "active_customers": active_customers,
            "pending_amount": round(float(pending_amount), 2),
            "available_amount": round(float(available_amount), 2),
            "paid_amount": round(float(paid_amount), 2),
        },
        "recent_commissions": [
            {
                "id": c.id,
                "plan": c.plan,
                "gross_amount": c.gross_amount,
                "commission_amount": c.commission_amount,
                "status": c.status,
                "billing_cycle": c.billing_cycle,
                "created_at": c.created_at.isoformat(),
            }
            for c in commissions
        ],
        "materials": [
            {
                "id": m.id,
                "title": m.title,
                "category": m.category,
                "content": m.content,
                "file_url": m.file_url,
            }
            for m in materials
        ]
    }