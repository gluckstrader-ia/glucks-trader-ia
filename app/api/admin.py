from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin_user
from app.models import User

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
        raise HTTPException(
            status_code=400,
            detail="ID do payload diferente do ID da rota",
        )

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
            raise HTTPException(
                status_code=400,
                detail="E-mail já está em uso por outro usuário",
            )

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