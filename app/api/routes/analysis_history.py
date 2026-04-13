from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.analysis_history import AnalysisHistory
from app.services.analysis_validation_service import validate_open_analyses

router = APIRouter(tags=["analysis_history"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _format_result_label(status: str) -> str:
    if status == "GAIN_TOTAL":
        return "Gain Total"
    if status == "GAIN_PARCIAL":
        return "Gain Parcial"
    if status == "LOSS":
        return "Loss"
    return "Em andamento"


@router.get("/analysis/recent")
def get_recent_analyses(db: Session = Depends(get_db)):
    # Valida as análises em aberto antes de retornar a lista
    validate_open_analyses(db, limit=100)

    analyses = (
        db.query(AnalysisHistory)
        .order_by(AnalysisHistory.created_at.desc())
        .limit(10)
        .all()
    )

    return [
        {
            "id": a.id,
            "asset": a.asset,
            "market": a.asset_type,
            "timeframe": a.timeframe,
            "signal": a.direction,
            "strength": round(float(a.confidence or 0.0), 1),
            "status": a.status,
            "resultLabel": _format_result_label(a.status),
            "resultDetail": a.result_detail,
            "createdAt": a.created_at.isoformat() if a.created_at else None,
            "entry": a.entry,
            "stop": a.stop,
            "tp1": a.tp1,
            "tp2": a.tp2,
            "tp3": a.tp3,
        }
        for a in analyses
    ]


@router.get("/analysis/all")
def get_all_recent_analyses(db: Session = Depends(get_db)):
    validate_open_analyses(db, limit=300)

    analyses = (
        db.query(AnalysisHistory)
        .order_by(AnalysisHistory.created_at.desc())
        .limit(50)
        .all()
    )

    return [
        {
            "id": a.id,
            "asset": a.asset,
            "market": a.asset_type,
            "timeframe": a.timeframe,
            "signal": a.direction,
            "strength": round(float(a.confidence or 0.0), 1),
            "status": a.status,
            "resultLabel": _format_result_label(a.status),
            "resultDetail": a.result_detail,
            "createdAt": a.created_at.isoformat() if a.created_at else None,
            "entry": a.entry,
            "stop": a.stop,
            "tp1": a.tp1,
            "tp2": a.tp2,
            "tp3": a.tp3,
        }
        for a in analyses
    ]


@router.post("/analysis/validate-open")
def force_validate_open_analyses(db: Session = Depends(get_db)):
    return validate_open_analyses(db, limit=500)