from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    plan = Column(String(50), nullable=False)
    amount = Column(Float, default=0.0, nullable=False)

    status = Column(String(30), default="pending", nullable=False)

    pagbank_checkout_id = Column(String(150), nullable=True, index=True)
    pagbank_order_id = Column(String(150), nullable=True, index=True)
    pagbank_reference_id = Column(String(150), nullable=True, unique=True, index=True)
    pagbank_payment_url = Column(String(500), nullable=True)

    partner_code = Column(String(50), nullable=True, index=True)
    partner_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    paid_at = Column(DateTime, nullable=True)