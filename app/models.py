from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)

    password_hash = Column(String(255), nullable=False)

    is_active = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    plan = Column(String(50), default="none")
    plan_status = Column(String(50), default="pending")

    access_expires_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    community_messages = relationship(
        "CommunityMessage",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    asset = Column(
        String(50),
        nullable=False,
    )

    asset_type = Column(
        String(50),
        nullable=False,
    )

    timeframe = Column(
        String(20),
        nullable=False,
    )

    signal = Column(
        String(50),
        nullable=True,
    )

    confidence = Column(
        Float,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user = relationship("User")


class CommunityMessage(Base):
    __tablename__ = "community_messages"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    user_name = Column(
        String(255),
        nullable=False,
    )

    channel = Column(
        String(50),
        nullable=False,
        index=True,
    )

    message_type = Column(
        String(20),
        nullable=False,
        default="text",
    )

    content = Column(
        Text,
        nullable=True,
    )

    media_url = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user = relationship(
        "User",
        back_populates="community_messages",
    )


# =====================================================
# AI MEMORY LAYER V2
# =====================================================

class AISignalMemory(Base):

    __tablename__ = "ai_signal_memory"


    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )


    asset = Column(
        String(50),
        nullable=False,
        index=True,
    )


    asset_type = Column(
        String(50),
        nullable=False,
    )


    timeframe = Column(
        String(20),
        nullable=False,
        index=True,
    )


    direction = Column(
        String(20),
        nullable=True,
    )


    signal_confidence = Column(
        String(50),
        nullable=True,
    )


    trade_quality_score = Column(
        Float,
        nullable=True,
    )


    trade_quality_label = Column(
        String(50),
        nullable=True,
    )


    module_alignment = Column(
        String(50),
        nullable=True,
        index=True,
    )


    decision_state = Column(
        String(50),
        nullable=True,
    )


    decision_color = Column(
        String(20),
        nullable=True,
    )


    entry = Column(
        Float,
        nullable=True,
    )


    stop = Column(
        Float,
        nullable=True,
    )


    target = Column(
        Float,
        nullable=True,
    )


    result = Column(
        String(20),
        nullable=True,
    )


    profit_points = Column(
        Float,
        nullable=True,
    )


    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


    closed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )