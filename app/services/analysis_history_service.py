from sqlalchemy.orm import Session
from app.models.analysis_history import AnalysisHistory


def save_analysis(db: Session, data: dict) -> AnalysisHistory:
    analysis = AnalysisHistory(
        asset=data["asset"],
        asset_type=data["asset_type"],
        timeframe=data["timeframe"],
        direction=data["direction"],
        confidence=data["confidence"],
        entry=data["entry"],
        stop=data["stop"],
        tp1=data["target"],
        tp2=data["summary"]["tp2"],
        tp3=data["summary"]["tp3"],
        status="EM_ANDAMENTO",
        result_detail="Aguardando fechamento",
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis