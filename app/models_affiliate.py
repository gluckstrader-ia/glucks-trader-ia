from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from app.database import Base


class AffiliateCommission(Base):
    __tablename__ = "affiliate_commissions"

    id = Column(Integer, primary_key=True, index=True)

    partner_user_id = Column(Integer, nullable=False, index=True)
    customer_user_id = Column(Integer, nullable=True, index=True)

    customer_name = Column(String(120), nullable=True)
    customer_email = Column(String(150), nullable=True)

    plan = Column(String(50), nullable=True)

    gross_amount = Column(Float, default=0.0, nullable=False)
    commission_percent = Column(Float, default=10.0, nullable=False)
    commission_amount = Column(Float, default=0.0, nullable=False)

    status = Column(String(30), default="pending", nullable=False)
    billing_cycle = Column(String(50), nullable=True)
    payment_reference = Column(String(150), nullable=True)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    available_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)


class AffiliateClick(Base):
    __tablename__ = "affiliate_clicks"

    id = Column(Integer, primary_key=True, index=True)

    partner_code = Column(String(50), nullable=False, index=True)
    landing_page = Column(String(500), nullable=True)
    ip = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AffiliateMaterial(Base):
    __tablename__ = "affiliate_materials"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(150), nullable=False)
    category = Column(String(80), nullable=True)
    content = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)