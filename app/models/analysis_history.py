from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.database import Base


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True)

    asset = Column(String, index=True)
    asset_type = Column(String)
    timeframe = Column(String)

    direction = Column(String)
    confidence = Column(Float)

    entry = Column(Float)
    stop = Column(Float)
    tp1 = Column(Float)
    tp2 = Column(Float)
    tp3 = Column(Float)

    status = Column(String, default="EM_ANDAMENTO")

    created_at = Column(DateTime, default=datetime.utcnow)