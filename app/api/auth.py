from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import (
    authenticate_user,
    create_access_token,
    get_user_by_email,
    get_user_by_id,
    hash_password,
    serialize_user,
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


@router.post("/auth/register", response_model=AuthResponse)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um usuário com este email",
        )

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
        pagbank_reference=None,
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


@router.post("/auth/login", response_model=AuthResponse)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos",
        )

    access_token = create_access_token(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": serialize_user(user),
    }


@router.get("/auth/me", response_model=UserResponse)
def auth_me(current_user: User = Depends(get_current_user)):
    return serialize_user(current_user)


@router.get("/auth/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    users = db.query(User).order_by(User.id.desc()).all()
    return [serialize_user(user) for user in users]


@router.patch("/auth/activate/{user_id}", response_model=UserStatusUpdateResponse)
def activate_user(
    user_id: int,
    payload: ActivateUserRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    selected_plan = (payload.plan or "mensal").lower().strip()

    if selected_plan not in PLAN_DURATIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plano inválido. Use: mensal, trimestral ou semestral.",
        )

    user.is_active = True
    user.is_blocked = False
    user.plan = selected_plan
    user.plan_status = "active"
    user.access_expires_at = datetime.utcnow() + timedelta(days=PLAN_DURATIONS[selected_plan])

    db.commit()
    db.refresh(user)

    return {
        "message": f"Usuário {user.name} ativado com sucesso",
        "user": serialize_user(user),
    }


@router.patch("/auth/renew/{user_id}", response_model=UserStatusUpdateResponse)
def renew_user(
    user_id: int,
    payload: RenewUserRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    selected_plan = (payload.plan or user.plan or "mensal").lower().strip()

    if selected_plan not in PLAN_DURATIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plano inválido. Use: mensal, trimestral ou semestral.",
        )

    base_date = datetime.utcnow()
    if user.access_expires_at and user.access_expires_at > base_date:
        base_date = user.access_expires_at

    user.is_active = True
    user.is_blocked = False
    user.plan = selected_plan
    user.plan_status = "active"
    user.access_expires_at = base_date + timedelta(days=PLAN_DURATIONS[selected_plan])

    db.commit()
    db.refresh(user)

    return {
        "message": f"Usuário {user.name} renovado com sucesso",
        "user": serialize_user(user),
    }


@router.patch("/auth/block/{user_id}", response_model=UserStatusUpdateResponse)
def block_user(
    user_id: int,
    payload: BlockUserRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.is_active = False
    user.is_blocked = True
    user.plan_status = "cancelled"

    db.commit()
    db.refresh(user)

    return {
        "message": f"Usuário {user.name} bloqueado com sucesso",
        "user": serialize_user(user),
    }


@router.patch("/auth/make-admin/{user_id}", response_model=UserStatusUpdateResponse)
def make_admin(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.is_admin = True

    db.commit()
    db.refresh(user)

    return {
        "message": f"Usuário {user.name} promovido para admin com sucesso",
        "user": serialize_user(user),
    }