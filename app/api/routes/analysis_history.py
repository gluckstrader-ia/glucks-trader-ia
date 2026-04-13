from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.analysis_history import AnalysisHistory

router = APIRouter(tags=["analysis_history"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/analysis/recent")
def get_recent_analyses(db: Session = Depends(get_db)):
    analyses = (
        db.query(AnalysisHistory)
        .order_by(AnalysisHistory.created_at.desc())
        .limit(10)
        .all()
    )

    return [
        {
            "asset": a.asset,
            "market": a.asset_type,
            "timeframe": a.timeframe,
            "signal": a.direction,
            "confidence": a.confidence,
            "status": a.status,
            "entry": a.entry,
            "stop": a.stop,
            "tp1": a.tp1,
            "tp2": a.tp2,
            "tp3": a.tp3,
            "created_at": a.created_at,
        }
        for a in analyses
    ]