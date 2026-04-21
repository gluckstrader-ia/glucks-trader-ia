from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.services.affiliate_service import (
    attach_partner_to_customer_by_code,
    create_recurring_commission,
    get_partner_dashboard_summary,
    get_partner_indications,
)

from app.auth import (
    authenticate_user,
    create_access_token,
    get_user_by_email,
    get_user_by_id,
    hash_password,
    serialize_user,
    generate_partner_code,
)

from app.database import get_db
from app.dependencies import get_current_admin_user, get_current_user
from app.models import User
from app.schemas_auth import (
    ActivateUserRequest,
    AuthResponse,
    BlockUserRequest,
    RenewUserRequest,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserStatusUpdateResponse,
)

router = APIRouter(tags=["auth"])

PLAN_DURATIONS = {
    "mensal": 30,
    "trimestral": 90,
    "semestral": 180,
}

PLAN_PRICES = {
    "mensal": 197.00,
    "trimestral": 497.00,
    "semestral": 897.00,
}

# =========================================
# CADASTRO CLIENTE
# =========================================
@router.post("/auth/register", response_model=AuthResponse)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(400, "Já existe um usuário com este email")

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        password_hash=hash_password(payload.password),
        is_active=True,
        is_blocked=False,
        is_admin=False,
        plan="trial",
        plan_status="active",
        access_expires_at=datetime.now(timezone.utc) + timedelta(days=5),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # VÍNCULO COM PARCEIRO
    try:
        if payload.referred_by_code:
            attach_partner_to_customer_by_code(
                db=db,
                customer=user,
                partner_code=payload.referred_by_code,
            )
    except Exception as e:
        print(f"[AFILIADO ERRO]: {e}")

    access_token = create_access_token(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": serialize_user(user),
    }


# =========================================
# CADASTRO PARCEIRO
# =========================================
@router.post("/auth/register-partner", response_model=AuthResponse)
def register_partner(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(400, "Já existe um usuário com este email")

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        password_hash=hash_password(payload.password),
        is_partner=True,
        partner_code=generate_partner_code(db, payload.name),
        partner_status="active",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": serialize_user(user),
    }


# =========================================
# LOGIN
# =========================================
@router.post("/auth/login", response_model=AuthResponse)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)

    if not user:
        raise HTTPException(401, "Email ou senha inválidos")

    access_token = create_access_token(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": serialize_user(user),
    }


@router.get("/auth/me", response_model=UserResponse)
def auth_me(current_user: User = Depends(get_current_user)):
    return serialize_user(current_user)


# =========================================
# DASHBOARD PARCEIRO (REAL)
# =========================================
@router.get("/auth/partner-dashboard")
def partner_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_partner:
        raise HTTPException(403, "Usuário não é parceiro")

    summary = get_partner_dashboard_summary(db, current_user.id)

    return {
        "partner_name": current_user.name,
        "partner_email": current_user.email,
        "partner_code": current_user.partner_code,
        "partner_status": current_user.partner_status,
        **summary,
    }


@router.get("/auth/partner-indications")
def partner_indications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_partner:
        raise HTTPException(403, "Usuário não é parceiro")

    return get_partner_indications(db, current_user.id)