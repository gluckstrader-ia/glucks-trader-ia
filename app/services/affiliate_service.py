import random
import string
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import User
from app.models_affiliate import AffiliateCommission


def normalize_code(name: str) -> str:
    base = "".join(ch for ch in (name or "").upper() if ch.isalnum())
    return base[:8] if base else "GLUCK"


def generate_partner_code(db: Session, name: str) -> str:
    prefix = normalize_code(name)

    while True:
        suffix = "".join(random.choices(string.digits, k=4))
        code = f"{prefix}{suffix}"

        exists = db.query(User).filter(User.partner_code == code).first()
        if not exists:
            return code


def create_partner_if_needed(db: Session, user: User):
    if user.is_partner and user.partner_code:
        return user

    user.is_partner = True
    user.partner_status = "active"
    user.partner_code = generate_partner_code(db, user.name)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def attach_partner_to_customer_by_code(db: Session, customer: User, partner_code: str | None):
    if not partner_code:
        return customer

    # Se já existe parceiro vinculado, não troca
    if customer.referred_by_user_id and customer.referred_by_code:
        return customer

    partner = db.query(User).filter(
        User.partner_code == partner_code,
        User.is_partner == True,
        User.partner_status == "active"
    ).first()

    if not partner:
        return customer

    customer.referred_by_user_id = partner.id
    customer.referred_by_code = partner.partner_code

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def create_recurring_commission(
    db: Session,
    customer: User,
    gross_amount: float,
    plan: str,
    payment_reference: str | None = None,
    external_order_id: str | None = None,
    billing_cycle: str = "recurring",
):
    if not customer.referred_by_user_id:
        return None

    commission_amount = round(gross_amount * 0.10, 2)

    commission = AffiliateCommission(
        partner_user_id=customer.referred_by_user_id,
        customer_user_id=customer.id,
        payment_reference=payment_reference,
        external_order_id=external_order_id,
        plan=plan,
        billing_cycle=billing_cycle,
        gross_amount=gross_amount,
        commission_percent=10.0,
        commission_amount=commission_amount,
        status="pending",
        available_at=datetime.utcnow() + timedelta(days=7),
    )

    db.add(commission)
    db.commit()
    db.refresh(commission)

    return commission


def release_weekly_commissions(db: Session):
    now = datetime.utcnow()

    commissions = db.query(AffiliateCommission).filter(
        AffiliateCommission.status == "pending",
        AffiliateCommission.available_at <= now
    ).all()

    for item in commissions:
        item.status = "available"
        db.add(item)

    db.commit()
    return len(commissions)