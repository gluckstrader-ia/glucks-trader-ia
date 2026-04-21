from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    is_active = Column(Boolean, default=False, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    plan = Column(String(50), default="none", nullable=False)
    plan_status = Column(String(50), default="pending", nullable=False)
    access_expires_at = Column(DateTime, nullable=True)

    pagbank_reference = Column(String(150), nullable=True)

    # =========================
    # Programa de parceiros
    # =========================
    is_partner = Column(Boolean, default=False, nullable=False)
    partner_code = Column(String(50), unique=True, index=True, nullable=True)
    partner_pix_key = Column(String(150), nullable=True)
    partner_pix_type = Column(String(30), nullable=True)  # cpf, email, telefone, aleatoria
    partner_status = Column(String(30), default="active", nullable=False)  # active, blocked

    # Usuário cliente indicado por parceiro
    referred_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    referred_by_code = Column(String(50), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class PartnerCommission(Base):
    __tablename__ = "partner_commissions"

    id = Column(Integer, primary_key=True, index=True)

    partner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    referred_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    sale_amount = Column(Float, default=0.0, nullable=False)
    commission_amount = Column(Float, default=0.0, nullable=False)

    plan = Column(String(50), nullable=True)
    status = Column(String(30), default="pending", nullable=False)  # pending, paid

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    paid_at = Column(DateTime, nullable=True)