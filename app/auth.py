from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from app.models import User

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    password = str(password).strip()
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    plain_password = str(plain_password).strip()
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(user: User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user.id),
        "email": user.email,
        "is_admin": user.is_admin,
        "exp": expire,
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email.lower().strip()).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def user_has_access(user: Optional[User]) -> bool:
    if not user:
        return False

    if not user.is_active:
        return False

    if user.is_blocked:
        return False

    if getattr(user, "plan_status", None) != "active":
        return False

    if not getattr(user, "access_expires_at", None):
        return False

    expires_at = user.access_expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return expires_at >= datetime.now(timezone.utc)


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "is_active": user.is_active,
        "is_blocked": user.is_blocked,
        "is_admin": user.is_admin,
        "plan": getattr(user, "plan", "none"),
        "plan_status": getattr(user, "plan_status", "pending"),
        "access_expires_at": user.access_expires_at.isoformat() if getattr(user, "access_expires_at", None) else None,
        "has_access": user_has_access(user),
        "created_at": user.created_at.isoformat() if getattr(user, "created_at", None) else None,
        "updated_at": user.updated_at.isoformat() if getattr(user, "updated_at", None) else None,
    }