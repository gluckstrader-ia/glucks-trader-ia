from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from app.models.analysis_history import AnalysisHistory
from app.services.market_data_service import get_market_data
from app.services.symbol_resolver import resolve_provider_symbol


OPEN_STATUSES = {"EM_ANDAMENTO"}


def _normalize_provider_symbol(asset: str, asset_type: str) -> str:
    asset = str(asset).upper().strip()
    asset_type = str(asset_type).lower().strip()

    if asset_type in {"future_us", "futuro_us", "futuros_us"}:
        return resolve_provider_symbol(asset, asset_type, "yfinance")

    if asset_type == "forex" and asset == "XAUUSD":
        return resolve_provider_symbol(asset, asset_type, "yfinance")

    return asset


def _prepare_market_data(analysis: AnalysisHistory) -> pd.DataFrame:
    provider_symbol = _normalize_provider_symbol(analysis.asset, analysis.asset_type)
    prefer_binance = analysis.asset_type == "crypto"

    df = get_market_data(
        asset=provider_symbol,
        asset_type=analysis.asset_type,
        timeframe=analysis.timeframe,
        prefer_binance=prefer_binance,
    )

    if df is None or df.empty:
        raise ValueError("Sem candles para validação")

    required_cols = {"high", "low"}
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes para validação: {missing}")

    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], utc=False, errors="coerce")
        df = df.dropna(subset=["datetime"]).copy()
        df = df.sort_values("datetime")
    elif isinstance(df.index, pd.DatetimeIndex):
        df = df.copy().sort_index()
        df["datetime"] = pd.to_datetime(df.index, utc=False, errors="coerce")
        df = df.dropna(subset=["datetime"]).copy()
    else:
        # fallback: sem timestamp explícito; ainda assim tentamos validar pela ordem
        df = df.copy()
        df["datetime"] = pd.NaT

    df["high"] = pd.to_numeric(df["high"], errors="coerce")
    df["low"] = pd.to_numeric(df["low"], errors="coerce")
    df = df.dropna(subset=["high", "low"]).copy()

    if df.empty:
        raise ValueError("Candles inválidos após limpeza")

    return df


def _filter_candles_after_analysis(df: pd.DataFrame, analysis_created_at: datetime) -> pd.DataFrame:
    if "datetime" not in df.columns or df["datetime"].isna().all():
        return df

    analysis_dt = pd.to_datetime(analysis_created_at, utc=False, errors="coerce")
    if pd.isna(analysis_dt):
        return df

    filtered = df[df["datetime"] >= analysis_dt].copy()
    return filtered if not filtered.empty else df


def _check_buy_outcome(row: pd.Series, tp1: float, tp3: float, stop: float, tp1_hit: bool) -> Tuple[Optional[str], bool]:
    high = float(row["high"])
    low = float(row["low"])

    # Já havia ganho parcial e agora bateu TP3
    if tp1_hit and high >= tp3:
        return "GAIN_TOTAL", True

    # Se ainda não bateu TP1
    if not tp1_hit:
        if high >= tp1:
            return "GAIN_PARCIAL", True

        if low <= stop:
            return "LOSS", False

        return None, False

    # Já bateu TP1 antes: enquanto não bater TP3, mantém parcial mesmo se depois voltar
    return None, False


def _check_sell_outcome(row: pd.Series, tp1: float, tp3: float, stop: float, tp1_hit: bool) -> Tuple[Optional[str], bool]:
    high = float(row["high"])
    low = float(row["low"])

    if tp1_hit and low <= tp3:
        return "GAIN_TOTAL", True

    if not tp1_hit:
        if low <= tp1:
            return "GAIN_PARCIAL", True

        if high >= stop:
            return "LOSS", False

        return None, False

    return None, False


def evaluate_analysis_outcome(df: pd.DataFrame, analysis: AnalysisHistory) -> Dict[str, Any]:
    candles = _filter_candles_after_analysis(df, analysis.created_at)

    tp1_hit = False

    for _, row in candles.iterrows():
        if analysis.direction == "COMPRA":
            outcome, partial = _check_buy_outcome(
                row=row,
                tp1=analysis.tp1,
                tp3=analysis.tp3,
                stop=analysis.stop,
                tp1_hit=tp1_hit,
            )
        elif analysis.direction == "VENDA":
            outcome, partial = _check_sell_outcome(
                row=row,
                tp1=analysis.tp1,
                tp3=analysis.tp3,
                stop=analysis.stop,
                tp1_hit=tp1_hit,
            )
        else:
            return {
                "status": "EM_ANDAMENTO",
                "result_detail": "Direção neutra sem validação operacional",
            }

        if partial:
            tp1_hit = True

        if outcome == "GAIN_TOTAL":
            return {
                "status": "GAIN_TOTAL",
                "result_detail": "3 alvos atingidos",
            }

        if outcome == "GAIN_PARCIAL":
            return {
                "status": "GAIN_PARCIAL",
                "result_detail": "TP1 atingido",
            }

        if outcome == "LOSS":
            return {
                "status": "LOSS",
                "result_detail": "Stop atingido",
            }

    # Se já bateu TP1 e não bateu TP3 depois, permanece ganho parcial
    if tp1_hit:
        return {
            "status": "GAIN_PARCIAL",
            "result_detail": "TP1 atingido",
        }

    return {
        "status": "EM_ANDAMENTO",
        "result_detail": "Aguardando fechamento",
    }


def validate_single_analysis(db: Session, analysis: AnalysisHistory) -> AnalysisHistory:
    if analysis.status not in OPEN_STATUSES:
        return analysis

    df = _prepare_market_data(analysis)
    result = evaluate_analysis_outcome(df, analysis)

    analysis.status = result["status"]
    analysis.result_detail = result["result_detail"]
    analysis.validated_at = datetime.utcnow()

    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def validate_open_analyses(db: Session, limit: int = 50) -> Dict[str, Any]:
    open_items = (
        db.query(AnalysisHistory)
        .filter(AnalysisHistory.status.in_(list(OPEN_STATUSES)))
        .order_by(AnalysisHistory.created_at.desc())
        .limit(limit)
        .all()
    )

    updated = 0
    errors = []

    for analysis in open_items:
        try:
            before = analysis.status
            validate_single_analysis(db, analysis)
            after = analysis.status
            if after != before:
                updated += 1
        except Exception as e:
            errors.append(
                {
                    "id": analysis.id,
                    "asset": analysis.asset,
                    "error": str(e),
                }
            )

    return {
        "checked": len(open_items),
        "updated": updated,
        "errors": errors,
    }