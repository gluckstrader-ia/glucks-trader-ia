from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    phone = Column(String(30), nullable=True)
    address_number = Column(String(20), nullable=True)

    is_active = Column(Boolean, default=False, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    plan = Column(String(50), default="none", nullable=False)
    plan_status = Column(String(50), default="pending", nullable=False)
    access_expires_at = Column(DateTime, nullable=True)

    pagbank_reference = Column(String(150), nullable=True)

    # Afiliados / parceiros
    is_partner = Column(Boolean, default=False, nullable=False)
    partner_code = Column(String(50), unique=True, index=True, nullable=True)
    partner_status = Column(String(30), default="active", nullable=False)
    partner_pix_key = Column(String(150), nullable=True)
    partner_pix_type = Column(String(30), nullable=True)

    # Cliente indicado por afiliado
    referred_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    referred_by_code = Column(String(50), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )