from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
)

from sqlalchemy.sql import func

from app.database import Base


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