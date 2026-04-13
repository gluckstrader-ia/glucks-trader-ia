from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String
from app.database import Base


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True)

    asset = Column(String, index=True, nullable=False)
    asset_type = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)

    direction = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)

    entry = Column(Float, nullable=False)
    stop = Column(Float, nullable=False)
    tp1 = Column(Float, nullable=False)
    tp2 = Column(Float, nullable=False)
    tp3 = Column(Float, nullable=False)

    status = Column(String, default="EM_ANDAMENTO", nullable=False)
    result_detail = Column(String, default="Aguardando fechamento", nullable=False)

    validated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)