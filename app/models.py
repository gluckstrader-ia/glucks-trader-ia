from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

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

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    provider = Column(String(50), default="pagbank", nullable=False)
    plan = Column(String(50), nullable=False)

    reference_id = Column(String(120), unique=True, nullable=False, index=True)
    external_id = Column(String(120), nullable=True, index=True)  # checkout_id ou order_id PagBank
    checkout_url = Column(String(500), nullable=True)

    status = Column(String(50), default="pending", nullable=False)
    amount = Column(Integer, nullable=False)  # em centavos
    raw_payload = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = relationship("User")    