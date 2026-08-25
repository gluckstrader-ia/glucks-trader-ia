from typing import Any, Dict, List


def clamp(
    value: float,
    minimum: float = 0,
    maximum: float = 100,
) -> float:
    return max(
        minimum,
        min(maximum, value),
    )


def safe_float(
    value: Any,
    default: float = 50.0,
) -> float:
    try:
        return float(value)
    except Exception:
        return default


def get_module_score(
    modules: Dict[str, Any],
    key: str,
    default: float = 50.0,
) -> float:

    return safe_float(
        modules.get(
            key,
            default,
        ),
        default,
    )


# =====================================================
# AI SCORE PRINCIPAL
# =====================================================


def calculate_ai_score(
    data: Dict[str, Any],
) -> float:

    modules = data.get(
        "modules",
        {},
    )

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


# =====================================================
# QUALIDADE DO CENÁRIO
# =====================================================


def calculate_trade_quality(
    data: Dict[str, Any],
) -> float:

    modules = data.get(
        "modules",
        {},
    )

    quality = calculate_ai_score(
        data
    )


    final_signal = data.get(
        "final_signal",
        {},
    )


    strength = str(
        final_signal.get(
            "strength",
            "",
        )
    ).upper()


    # Penaliza sinal fraco

    if strength == "FRACA":
        quality -= 15


    # Penaliza baixa confluência

    confluence = safe_float(
        final_signal.get(
            "confluence_score",
            50,
        )
    )


    if confluence < 55:
        quality -= 15


    # Penaliza SMC sem confirmação

    smc = get_module_score(
        modules,
        "smc",
    )

    if smc < 50:
        quality -= 10


    # Penaliza probabilidade baixa

    probability = get_module_score(
        modules,
        "probabilistic",
    )

    if probability < 55:
        quality -= 10


    return round(
        clamp(quality),
        1,
    )


# =====================================================
# CLASSIFICAÇÃO
# =====================================================


def classify_quality(
    score: float,
) -> str:

    if score >= 85:
        return "EXCELENTE"

    if score >= 70:
        return "ALTA"

    if score >= 55:
        return "MODERADA"

    return "BAIXA"



def calculate_grade(
    score: float,
) -> str:

    if score >= 85:
        return "A+"

    if score >= 75:
        return "A"

    if score >= 60:
        return "B"

    if score >= 45:
        return "C"

    return "D"



# =====================================================
# DECISÃO OPERACIONAL
# =====================================================


def generate_recommendation(
    trade_quality: float,
    data: Dict[str, Any],
):

    direction = str(
        data.get(
            "direction",
            "NEUTRO",
        )
    ).upper()


    if trade_quality < 55:

        return {
            "recommendation":
                "AGUARDAR",

            "entry_allowed":
                False,

            "next_action":
                "Aguardar confirmação ou rompimento",
        }


    if direction == "COMPRA":

        return {
            "recommendation":
                "COMPRA AUTORIZADA",

            "entry_allowed":
                True,

            "next_action":
                "Monitorar entrada e gestão de risco",
        }


    if direction == "VENDA":

        return {
            "recommendation":
                "VENDA AUTORIZADA",

            "entry_allowed":
                True,

            "next_action":
                "Monitorar entrada e gestão de risco",
        }


    return {
        "recommendation":
            "AGUARDAR",

        "entry_allowed":
            False,

        "next_action":
            "Esperar definição do mercado",
    }



# =====================================================
# EXPLICAÇÃO
# =====================================================


def generate_reasons(
    data: Dict[str, Any],
) -> List[str]:

    reasons = []


    modules = data.get(
        "modules",
        {},
    )


    final_signal = data.get(
        "final_signal",
        {},
    )


    if get_module_score(
        modules,
        "technical",
    ) >= 70:

        reasons.append(
            "Confluência técnica favorável"
        )


    if get_module_score(
        modules,
        "smc",
    ) >= 70:

        reasons.append(
            "Smart Money confirmado"
        )


    if final_signal.get(
        "filter_reasons"
    ):

        reasons.extend(
            final_signal[
                "filter_reasons"
            ]
        )


    if not reasons:

        reasons.append(
            "Sem vantagem estatística clara"
        )


    return reasons



def generate_warnings(
    data: Dict[str, Any],
) -> List[str]:

    warnings = []


    context = data.get(
        "market_context",
        {},
    )


    if context.get(
        "zone_label"
    ) == "Premium":

        warnings.append(
            "Preço em região Premium"
        )


    return warnings



# =====================================================
# FUNÇÃO PRINCIPAL
# =====================================================


def build_ai_brain(
    data: Dict[str, Any],
) -> Dict[str, Any]:


    ai_score = calculate_ai_score(
        data
    )


    trade_quality = calculate_trade_quality(
        data
    )


    recommendation = generate_recommendation(
        trade_quality,
        data,
    )


    return {

        "score":
            ai_score,


        "quality":
            classify_quality(
                ai_score
            ),


        "trade_quality_score":
            trade_quality,


        "grade":
            calculate_grade(
                trade_quality
            ),


        "decision":
            data.get(
                "direction",
                "NEUTRO",
            ),


        "recommendation":
            recommendation[
                "recommendation"
            ],


        "entry_allowed":
            recommendation[
                "entry_allowed"
            ],


        "next_action":
            recommendation[
                "next_action"
            ],


        "market_state":
            (
                "INDECISÃO"
                if not recommendation["entry_allowed"]
                else "OPORTUNIDADE"
            ),


        "reasons":
            generate_reasons(
                data
            ),


        "warnings":
            generate_warnings(
                data
            ),
    }