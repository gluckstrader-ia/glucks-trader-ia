from datetime import datetime, timedelta, timezone
import random
import string
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
        "is_partner": bool(getattr(user, "is_partner", False)),
        "exp": expire,
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email.lower().strip()).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_partner_code(db: Session, partner_code: str) -> Optional[User]:
    code = str(partner_code or "").strip().upper()
    if not code:
        return None

    return (
        db.query(User)
        .filter(
            User.partner_code == code,
            User.is_partner == True,
        )
        .first()
    )


def partner_code_exists(db: Session, partner_code: str) -> bool:
    return get_user_by_partner_code(db, partner_code) is not None


def generate_partner_code(db: Session, name: str) -> str:
    base = "".join(ch for ch in str(name).upper() if ch.isalnum())[:6]
    if not base:
        base = "PARC"

    while True:
        suffix = "".join(random.choices(string.digits, k=4))
        code = f"{base}{suffix}"

        exists = db.query(User).filter(User.partner_code == code).first()
        if not exists:
            return code


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
    referred_by_user_id = getattr(user, "referred_by_user_id", None)
    referred_by_code = getattr(user, "referred_by_code", None)

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,

        "phone": getattr(user, "phone", None),
        "address_number": getattr(user, "address_number", None),

        "is_active": bool(user.is_active),
        "is_blocked": bool(user.is_blocked),
        "is_admin": bool(user.is_admin),

        "plan": getattr(user, "plan", "none"),
        "plan_status": getattr(user, "plan_status", "pending"),

        "access_expires_at": (
            user.access_expires_at.isoformat()
            if getattr(user, "access_expires_at", None)
            else None
        ),

        "has_access": bool(user_has_access(user)),

        "created_at": (
            user.created_at.isoformat()
            if getattr(user, "created_at", None)
            else None
        ),
        "updated_at": (
            user.updated_at.isoformat()
            if getattr(user, "updated_at", None)
            else None
        ),

        "is_partner": bool(getattr(user, "is_partner", False)),
        "partner_code": getattr(user, "partner_code", None),
        "partner_status": getattr(user, "partner_status", "inactive"),
        "partner_pix_key": getattr(user, "partner_pix_key", None),
        "partner_pix_type": getattr(user, "partner_pix_type", None),

        "referred_by_user_id": referred_by_user_id,
        "referred_by_code": referred_by_code,

        #"referred_by_code": getattr(user, "referred_by_code", None),
        #"affiliate_code": getattr(user, "referred_by_code", None),

        "affiliate_code": referred_by_code,
    }