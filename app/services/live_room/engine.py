from datetime import datetime

from app.services.analysis_service import analyze_asset
from app.services.live_room.schemas import (
    LiveRoomAlert,
    LiveRoomResponse,
    LiveRoomScenarioMemory,
    LiveRoomStateFlags,
)
from app.services.live_room.market_state import validate_live_asset, SUPPORTED_LIVE_ASSETS


LAST_SCENARIOS: dict[str, dict] = {}


def map_asset_type(asset: str) -> str:
    return SUPPORTED_LIVE_ASSETS[asset]["market"]


def map_signal(direction: str) -> str:
    if direction == "COMPRA":
        return "buy"
    elif direction == "VENDA":
        return "sell"
    elif direction == "NEUTRO":
        return "neutral"
    return "wait"


def confidence_label(confidence: float) -> str:
    if confidence >= 80:
        return "alta"
    if confidence >= 65:
        return "moderada"
    return "baixa"


def regime_label(summary_trend_label: str) -> str:
    value = (summary_trend_label or "").upper()
    if value == "ALTA":
        return "viés de alta"
    if value == "BAIXA":
        return "viés de baixa"
    return "mercado mais neutro"


def format_price(value):
    if value is None:
        return None
    try:
        value = float(value)
        if abs(value) >= 1000:
            return f"{value:.0f}"
        elif abs(value) >= 100:
            return f"{value:.2f}"
        else:
            return f"{value:.5f}"
    except Exception:
        return str(value)


def safe_float(value, default=0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def compute_event_context(analysis: dict) -> dict:
    direction = analysis["direction"]
    current_price = safe_float(analysis["market_context"]["current_price"])
    entry = safe_float(analysis.get("entry"), current_price)
    stop = safe_float(analysis.get("stop"), current_price)
    target = safe_float(analysis.get("target"), current_price)
    nearest_support = safe_float(analysis["market_context"]["nearest_support"], current_price)
    nearest_resistance = safe_float(analysis["market_context"]["nearest_resistance"], current_price)
    rsi = safe_float(analysis["technical"]["rsi"], 50.0)
    confidence = safe_float(analysis["confidence"], 50.0)

    dist_to_target = abs(target - current_price)
    dist_to_stop = abs(stop - current_price)
    dist_to_support = abs(current_price - nearest_support)
    dist_to_resistance = abs(nearest_resistance - current_price)

    total_target_leg = max(abs(target - entry), 1e-9)
    total_stop_leg = max(abs(entry - stop), 1e-9)

    near_target = dist_to_target <= total_target_leg * 0.20
    near_stop = dist_to_stop <= total_stop_leg * 0.20

    entry_zone = abs(current_price - entry) <= max(total_stop_leg * 0.20, 1e-9)

    losing_strength = False
    strengthening = False
    neutral_market = direction == "NEUTRO"

    if direction == "COMPRA":
        strengthening = confidence >= 70 and rsi >= 55 and dist_to_stop > dist_to_target
        losing_strength = rsi < 52 or dist_to_resistance < dist_to_support
    elif direction == "VENDA":
        strengthening = confidence >= 70 and rsi <= 45 and dist_to_stop > dist_to_target
        losing_strength = rsi > 48 or dist_to_support < dist_to_resistance

    return {
        "near_target": near_target,
        "near_stop": near_stop,
        "entry_zone": entry_zone,
        "strengthening": strengthening,
        "losing_strength": losing_strength,
        "neutral_market": neutral_market,
    }


def build_memory(asset: str, signal: str, confidence: int) -> LiveRoomScenarioMemory:
    previous = LAST_SCENARIOS.get(asset)

    previous_signal = previous["signal"] if previous else None
    previous_confidence = previous["confidence"] if previous else None

    changed = previous_signal is not None and previous_signal != signal
    confidence_delta = 0 if previous_confidence is None else confidence - previous_confidence

    if previous is None:
        evolution_label = "cenário inicial"
    elif changed:
        evolution_label = "mudança de direção"
    elif confidence_delta >= 8:
        evolution_label = "cenário ganhou força"
    elif confidence_delta <= -8:
        evolution_label = "cenário perdeu força"
    else:
        evolution_label = "cenário mantido"

    LAST_SCENARIOS[asset] = {
        "signal": signal,
        "confidence": confidence,
    }

    return LiveRoomScenarioMemory(
        previous_signal=previous_signal,
        current_signal=signal,
        changed=changed,
        previous_confidence=previous_confidence,
        current_confidence=confidence,
        confidence_delta=confidence_delta,
        evolution_label=evolution_label,
    )


def build_alerts(analysis: dict, event_ctx: dict, memory: LiveRoomScenarioMemory) -> list[LiveRoomAlert]:
    alerts: list[LiveRoomAlert] = []

    if memory.changed:
        alerts.append(
            LiveRoomAlert(
                type="direction_change",
                title="MUDANÇA DE DIREÇÃO",
                message="A leitura mudou em relação ao cenário anterior.",
                priority=5,
            )
        )

    if event_ctx["entry_zone"] and analysis["direction"] in {"COMPRA", "VENDA"}:
        alerts.append(
            LiveRoomAlert(
                type="entry_alert",
                title="ALERTA DE ENTRADA",
                message="O preço está trabalhando na região de entrada sugerida.",
                priority=5,
            )
        )

    if event_ctx["near_stop"]:
        alerts.append(
            LiveRoomAlert(
                type="stop_threat",
                title="STOP AMEAÇADO",
                message="O preço se aproxima do ponto de invalidação do cenário.",
                priority=5,
            )
        )

    if event_ctx["near_target"]:
        alerts.append(
            LiveRoomAlert(
                type="target_near",
                title="ALVO PRÓXIMO",
                message="O preço está próximo do alvo projetado.",
                priority=4,
            )
        )

    if event_ctx["strengthening"]:
        alerts.append(
            LiveRoomAlert(
                type="strengthening",
                title="CONTINUIDADE DO CENÁRIO",
                message="A leitura mostra reforço da direção atual.",
                priority=3,
            )
        )

    if event_ctx["losing_strength"]:
        alerts.append(
            LiveRoomAlert(
                type="weakening",
                title="PERDA DE FORÇA",
                message="O cenário perdeu qualidade e exige confirmação.",
                priority=4,
            )
        )

    if not alerts:
        alerts.append(
            LiveRoomAlert(
                type="neutral",
                title="MONITORAMENTO",
                message="Mercado em acompanhamento, sem alerta crítico agora.",
                priority=1,
            )
        )

    alerts.sort(key=lambda item: item.priority, reverse=True)
    return alerts[:3]


def build_events(analysis: dict, memory: LiveRoomScenarioMemory, alerts: list[LiveRoomAlert]) -> list[str]:
    events = [
        f"Evolução: {memory.evolution_label}",
        f"Direção atual: {analysis['direction']}",
        f"Confiança atual: {analysis['confidence']:.1f}%",
        f"Confluência: {analysis['final_signal']['confluence_score']:.1f}",
        f"Preço atual: {format_price(analysis['market_context']['current_price'])}",
        f"Zona de mercado: {analysis['market_context']['zone_label']}",
    ]

    for alert in alerts[:2]:
        events.insert(0, alert.title)

    return events[:7]


def build_state_flags(analysis: dict, event_ctx: dict) -> LiveRoomStateFlags:
    direction = analysis["direction"]
    zone_label = analysis["market_context"]["zone_label"]

    return LiveRoomStateFlags(
        trend_up=direction == "COMPRA",
        trend_down=direction == "VENDA",
        lateralized=direction == "NEUTRO",
        above_vwap=False,
        exhaustion=zone_label == "Premium" and direction == "COMPRA" and event_ctx["losing_strength"],
    )


def build_narration(analysis: dict, memory: LiveRoomScenarioMemory, alerts: list[LiveRoomAlert]) -> str:
    asset = analysis["asset"]
    timeframe = analysis["timeframe"]
    direction = analysis["direction"]
    confidence = float(analysis["confidence"])
    confidence_text = confidence_label(confidence)
    trend_text = regime_label(analysis["summary"]["trend_label"])
    zone_label = analysis["market_context"]["zone_label"].lower()
    price_text = format_price(analysis["market_context"]["current_price"])
    entry_text = format_price(analysis.get("entry"))
    stop_text = format_price(analysis.get("stop"))
    target_text = format_price(analysis.get("target"))

    lead_alert = alerts[0].title if alerts else "MONITORAMENTO"

    memory_phrase = {
        "cenário inicial": "É a leitura inicial desta sala.",
        "mudança de direção": "O cenário mudou em relação à atualização anterior.",
        "cenário ganhou força": "A leitura ganhou força desde a última atualização.",
        "cenário perdeu força": "A leitura perdeu força em relação ao cenário anterior.",
        "cenário mantido": "O cenário anterior segue em manutenção.",
    }.get(memory.evolution_label, "O cenário segue em acompanhamento.")

    if direction == "COMPRA":
        return (
            f"{asset} segue no gráfico de {timeframe} com {trend_text} e confiança {confidence_text}. "
            f"O preço trabalha em {price_text}, em zona {zone_label}. "
            f"A leitura favorece compra, com entrada em {entry_text}, stop em {stop_text} e alvo em {target_text}. "
            f"{memory_phrase} Alerta principal do momento: {lead_alert}."
        )

    if direction == "VENDA":
        return (
            f"{asset} segue no gráfico de {timeframe} com {trend_text} e confiança {confidence_text}. "
            f"O preço trabalha em {price_text}, em zona {zone_label}. "
            f"A leitura favorece venda, com entrada em {entry_text}, stop em {stop_text} e alvo em {target_text}. "
            f"{memory_phrase} Alerta principal do momento: {lead_alert}."
        )

    return (
        f"{asset} está em monitoramento no gráfico de {timeframe}, com leitura mais neutra e confiança {confidence_text}. "
        f"O preço atual está em {price_text}, em zona {zone_label}. "
        f"{memory_phrase} Alerta principal do momento: {lead_alert}."
    )


def analyze_live_room_asset(asset: str, timeframe: str = "5m") -> LiveRoomResponse:
    asset = validate_live_asset(asset)
    asset_type = map_asset_type(asset)

    analysis = analyze_asset(
        asset=asset,
        asset_type=asset_type,
        timeframe=timeframe,
    )

    signal = map_signal(analysis["direction"])
    confidence = int(round(float(analysis["confidence"])))

    memory = build_memory(asset=asset, signal=signal, confidence=confidence)
    event_ctx = compute_event_context(analysis)
    alerts = build_alerts(analysis, event_ctx, memory)
    narration = build_narration(analysis, memory, alerts)
    events = build_events(analysis, memory, alerts)
    state_flags = build_state_flags(analysis, event_ctx)

    return LiveRoomResponse(
        asset=asset,
        timeframe=timeframe,
        price=analysis["market_context"]["current_price"],
        signal=signal,
        confidence=confidence,
        market_regime=analysis["summary"]["trend_label"],
        narration_text=narration,
        entry=analysis["entry"],
        stop=analysis["stop"],
        target_1=analysis["target"],
        target_2=analysis["summary"]["tp2"],
        risk_reward=analysis["risk_reward"],
        events=events,
        alerts=alerts,
        scenario_memory=memory,
        state_flags=state_flags,
        updated_at=datetime.utcnow(),
    )