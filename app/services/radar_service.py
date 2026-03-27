from typing import Any, Dict, List

from app.services.analysis_service import analyze_asset


DEFAULT_CRYPTO_ASSETS = [
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    "BNB-USD",
    "XRP-USD",
    "ADA-USD",
    "DOGE-USD",
    "AVAX-USD",
    "LINK-USD",
    "DOT-USD",
]


def build_scan_item(asset: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
    summary_obj = analysis.get("summary", {})
    final_signal = analysis.get("final_signal", {})

    return {
        "asset": asset.replace("-USD", "USDT"),
        "raw_asset": asset,
        "asset_type": "crypto",
        "timeframe": analysis.get("timeframe"),
        "direction": analysis.get("direction", "NEUTRO"),
        "score": analysis.get("score", 0),
        "confidence": analysis.get("confidence", 0),
        "entry": analysis.get("entry", 0),
        "stop": analysis.get("stop", 0),
        "target": analysis.get("target", 0),
        "risk_reward": analysis.get("risk_reward", 0),
        "signal_label": summary_obj.get("signal_label", analysis.get("direction", "NEUTRO")),
        "trend_label": summary_obj.get("trend_label", "NEUTRO"),
        "technical_label": summary_obj.get("technical_label", "NEUTRO"),
        "smart_money_label": summary_obj.get("smart_money_label", "NEUTRO"),
        "strength": final_signal.get("strength", "FRACA"),
        "verdict": final_signal.get("verdict", ""),
        "summary": f"Sinal {analysis.get('direction', 'NEUTRO')} com score {analysis.get('score', 0)}.",
    }


def scan_crypto_market(timeframe: str = "5m", limit: int = 10) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    for asset in DEFAULT_CRYPTO_ASSETS:
        try:
            analysis = analyze_asset(
                asset=asset,
                asset_type="crypto",
                timeframe=timeframe,
            )

            item = build_scan_item(asset, analysis)
            results.append(item)

        except Exception as e:
            print(f"[RADAR] Falha ao analisar {asset}: {e}")

    results.sort(
        key=lambda x: (x.get("score", 0), x.get("confidence", 0)),
        reverse=True
    )

    return results[:limit]