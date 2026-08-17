from datetime import datetime, timezone
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.services.affiliate_service import (
    attach_partner_to_customer_by_code,
    create_recurring_commission,
    get_partner_dashboard_summary,
    get_partner_indications,
)

from app.services.trial_calendar_service import calculate_trial_expiration

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

print("DEBUG USER MODEL FILE:", User.__module__)
print("DEBUG USER HAS referred_by_code:", hasattr(User, "referred_by_code"))
print("DEBUG USER HAS referred_by_user_id:", hasattr(User, "referred_by_user_id"))

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


def only_numbers(value: str | None) -> str:
    if not value:
        return ""

    return re.sub(r"\D", "", value)


def is_valid_brazilian_phone(phone: str | None) -> bool:
    phone = only_numbers(phone)

    if len(phone) not in [10, 11]:
        return False

    if len(set(phone)) == 1:
        return False

    fake_numbers = {
        "0000000000",
        "9999999999",
        "00000000000",
        "99999999999",
        "1234567890",
        "12345678901",
        "0123456789",
        "01234567890",
    }

    if phone in fake_numbers:
        return False

    if len(phone) == 11 and phone[2] != "9":
        return False

    return True


# =========================================
# CADASTRO CLIENTE
# =========================================
@router.post("/auth/register", response_model=AuthResponse)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = get_user_by_email(db, payload.email)

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Já existe um usuário com este email",
        )

    phone_clean = only_numbers(payload.phone)

    if not is_valid_brazilian_phone(phone_clean):
        raise HTTPException(
            status_code=400,
            detail="Telefone/WhatsApp inválido. Informe um número real com DDD.",
        )

    # Código digitado manualmente pelo cliente
    raw_code = payload.referred_by_code or payload.partner_code

    referred_by_code = None

    if raw_code:
        referred_by_code = (
            str(raw_code)
            .strip()
            .upper()
            .replace(" ", "")
            .replace("-", "")
            .replace("_", "")
        )

    # =========================================
    # TRIAL DE 5 PREGÕES DA B3
    # =========================================
    #
    # A expiração não é mais calculada em dias corridos.
    #
    # A função calculate_trial_expiration:
    #
    # - considera 5 pregões reais;
    # - ignora sábado e domingo;
    # - ignora dias sem sessão no calendário BVMF;
    # - considera o horário de abertura da bolsa;
    # - se o usuário se cadastrar depois da abertura,
    #   o pregão parcial não consome um dos 5 pregões completos;
    # - encerra o acesso no fechamento do 5º pregão.
    #
    trial_expires_at = calculate_trial_expiration(
        started_at=datetime.now(timezone.utc),
        sessions=5,
    )

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        password_hash=hash_password(payload.password),
        phone=phone_clean,
        address_number=(
            payload.address_number.strip()
            if payload.address_number
            else None
        ),
        is_active=True,
        is_blocked=False,
        is_admin=False,
        plan="trial",
        plan_status="active",
        access_expires_at=trial_expires_at,

        # Salva o código digitado pelo cliente
        referred_by_code=referred_by_code,
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
# CADASTRO PARCEIRO
# =========================================
@router.post("/auth/register-partner", response_model=AuthResponse)
def register_partner(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = get_user_by_email(db, payload.email)

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Já existe um usuário com este email",
        )

    phone_clean = only_numbers(payload.phone)

    if not is_valid_brazilian_phone(phone_clean):
        raise HTTPException(
            status_code=400,
            detail="Telefone/WhatsApp inválido. Informe um número real com DDD.",
        )

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        password_hash=hash_password(payload.password),
        phone=phone_clean,
        address_number=(
            payload.address_number.strip()
            if payload.address_number
            else None
        ),
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
def login(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        payload.email,
        payload.password,
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Email ou senha inválidos",
        )

    access_token = create_access_token(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": serialize_user(user),
    }


# =========================================
# USUÁRIO ATUAL
# =========================================
@router.get("/auth/me", response_model=UserResponse)
def auth_me(
    current_user: User = Depends(get_current_user),
):
    return serialize_user(current_user)


# =========================================
# DASHBOARD PARCEIRO
# =========================================
@router.get("/auth/partner-dashboard")
def partner_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_partner:
        raise HTTPException(
            status_code=403,
            detail="Usuário não é parceiro",
        )

    summary = get_partner_dashboard_summary(
        db,
        current_user.id,
    )

    return {
        "partner_name": current_user.name,
        "partner_email": current_user.email,
        "partner_code": current_user.partner_code,
        "partner_status": current_user.partner_status,
        **summary,
    }


# =========================================
# INDICAÇÕES DO PARCEIRO
# =========================================
@router.get("/auth/partner-indications")
def partner_indications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_partner:
        raise HTTPException(
            status_code=403,
            detail="Usuário não é parceiro",
        )

    return get_partner_indications(
        db,
        current_user.id,
    )