from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.database import Base


class AffiliateCommission(Base):
    __tablename__ = "affiliate_commissions"

    id = Column(Integer, primary_key=True, index=True)

    partner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    customer_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    payment_reference = Column(String(150), nullable=True, index=True)
    external_order_id = Column(String(150), nullable=True, index=True)

    plan = Column(String(50), nullable=False)
    billing_cycle = Column(String(30), nullable=False, default="recurring")
    # first_payment | recurring

    gross_amount = Column(Float, nullable=False)
    commission_percent = Column(Float, nullable=False, default=10.0)
    commission_amount = Column(Float, nullable=False)

    status = Column(String(30), nullable=False, default="pending")
    # pending | available | paid | canceled

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    available_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)


class AffiliateClick(Base):
    __tablename__ = "affiliate_clicks"

    id = Column(Integer, primary_key=True, index=True)
    partner_code = Column(String(50), nullable=False, index=True)
    landing_page = Column(String(255), nullable=True)
    ip = Column(String(100), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AffiliateMaterial(Base):
    __tablename__ = "affiliate_materials"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)  # whatsapp, instagram, roteiro, email, banner
    content = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)