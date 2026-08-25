from typing import Any, Dict, List


def clamp(value: float, minimum: float = 0, maximum: float = 100) -> float:
    """
    Mantém valores dentro de um intervalo seguro.
    """
    return max(minimum, min(maximum, value))


def get_module_score(
    modules: Dict[str, Any],
    key: str,
    default: float = 50.0,
) -> float:
    """
    Recupera um score de módulo evitando erros
    quando algum dado não existir.
    """
    try:
        return float(modules.get(key, default))
    except Exception:
        return default


def calculate_ai_score(data: Dict[str, Any]) -> float:
    """
    Calcula o score consolidado da inteligência artificial.

    Importante:
    Este score NÃO substitui o sinal original.
    Ele apenas mede a qualidade do cenário.
    """

    modules = data.get("modules", {})

    technical = get_module_score(
        modules,
        "technical",
    )

    smc = get_module_score(
        modules,
        "smc",
    )

    probabilistic = get_module_score(
        modules,
        "probabilistic",
    )

    timing = get_module_score(
        modules,
        "timing",
    )

    score = (
        technical * 0.35
        + smc * 0.25
        + probabilistic * 0.25
        + timing * 0.15
    )

    return round(
        clamp(score),
        1,
    )


def classify_quality(score: float) -> str:
    """
    Classifica a qualidade do cenário.
    """

    if score >= 85:
        return "EXCELENTE"

    if score >= 70:
        return "ALTA"

    if score >= 55:
        return "MODERADA"

    return "BAIXA"


def generate_reasons(
    data: Dict[str, Any],
) -> List[str]:
    """
    Cria explicações positivas para o usuário.
    """

    reasons = []

    modules = data.get(
        "modules",
        {},
    )

    technical = data.get(
        "technical",
        {},
    )

    if get_module_score(modules, "technical") >= 70:
        reasons.append(
            "Confluência técnica favorável"
        )

    if get_module_score(modules, "smc") >= 70:
        reasons.append(
            "Smart Money confirmou o cenário"
        )

    if get_module_score(modules, "probabilistic") >= 70:
        reasons.append(
            "Probabilidade estatística positiva"
        )

    trend = str(
        technical.get(
            "trend_bias",
            "",
        )
    ).upper()

    if trend == "ALTA":
        reasons.append(
            "Tendência compradora identificada"
        )

    elif trend == "BAIXA":
        reasons.append(
            "Tendência vendedora identificada"
        )

    return reasons


def generate_warnings(
    data: Dict[str, Any],
) -> List[str]:
    """
    Gera alertas de risco.
    """

    warnings = []

    modules = data.get(
        "modules",
        {},
    )

    market_context = data.get(
        "market_context",
        {},
    )

    timing = get_module_score(
        modules,
        "timing",
    )

    if timing < 60:
        warnings.append(
            "Momento de entrada exige cautela"
        )

    zone = str(
        market_context.get(
            "zone_label",
            "",
        )
    )

    if zone.upper() == "PREMIUM":
        warnings.append(
            "Preço próximo de região esticada"
        )

    if zone.upper() == "DESCONTO":
        warnings.append(
            "Entrada em região favorável de preço"
        )

    return warnings


def calculate_confidence(
    data: Dict[str, Any],
    ai_score: float,
) -> float:
    """
    Combina confiança original do motor
    com qualidade geral do cenário.
    """

    original_confidence = data.get(
        "confidence",
        50,
    )

    try:
        original_confidence = float(
            original_confidence
        )
    except Exception:
        original_confidence = 50.0

    confidence = (
        original_confidence * 0.60
        + ai_score * 0.40
    )

    return round(
        clamp(confidence),
        1,
    )


def build_ai_brain(
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Função principal do AI Brain.

    Recebe o resultado do analysis_service
    e retorna uma camada inteligente.
    """

    ai_score = calculate_ai_score(
        data
    )

    final_signal = data.get(
        "final_signal",
        {},
    )

    return {
        "score": ai_score,

        "quality": classify_quality(
            ai_score
        ),

        "confidence": calculate_confidence(
            data,
            ai_score,
        ),

        "decision": data.get(
            "direction",
            "NEUTRO",
        ),

        "strength": final_signal.get(
            "strength",
            "MODERADA",
        ),

        "reasons": generate_reasons(
            data
        ),

        "warnings": generate_warnings(
            data
        ),
    }