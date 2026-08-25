from typing import Any, Dict, List


# =====================================================
# HELPERS
# =====================================================

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
    default: float = 50,
) -> float:

    try:
        return float(value)

    except Exception:
        return default


def module_score(
    modules: Dict[str, Any],
    key: str,
) -> float:

    return safe_float(
        modules.get(
            key,
            50,
        )
    )


# =====================================================
# AI SCORE
# =====================================================

def calculate_ai_score(
    data: Dict[str, Any],
) -> float:

    modules = data.get(
        "modules",
        {},
    )

    score = (

        module_score(
            modules,
            "technical",
        ) * 0.35

        +

        module_score(
            modules,
            "smc",
        ) * 0.25

        +

        module_score(
            modules,
            "probabilistic",
        ) * 0.25

        +

        module_score(
            modules,
            "timing",
        ) * 0.15
    )

    return round(
        clamp(score),
        1,
    )


# =====================================================
# TRADE QUALITY
# =====================================================

def calculate_trade_quality(
    data: Dict[str, Any],
) -> float:

    quality = calculate_ai_score(
        data
    )

    modules = data.get(
        "modules",
        {},
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


    if strength == "FRACA":
        quality -= 15


    if module_score(
        modules,
        "smc",
    ) < 50:

        quality -= 10


    if module_score(
        modules,
        "probabilistic",
    ) < 55:

        quality -= 10


    return round(
        clamp(quality),
        1,
    )


# =====================================================
# DETECÇÃO DE CONFLITOS
# =====================================================

def detect_market_conflict(
    data: Dict[str, Any],
) -> Dict[str, Any]:

    conflicts = []

    direction = str(
        data.get(
            "direction",
            "NEUTRO",
        )
    ).upper()


    modules = data.get(
        "modules",
        {},
    )

    smc = data.get(
        "smc",
        {},
    )

    context = data.get(
        "market_context",
        {},
    )


    smc_bias = str(
        smc.get(
            "bias",
            "",
        )
    ).upper()


    zone = str(
        context.get(
            "zone_label",
            "",
        )
    ).upper()



    if direction == "COMPRA":

        if smc_bias in [
            "BEARISH",
            "BAIXA",
        ]:

            conflicts.append(
                "SMC divergente da compra"
            )


    if direction == "VENDA":

        if smc_bias in [
            "BULLISH",
            "ALTA",
        ]:

            conflicts.append(
                "SMC divergente da venda"
            )


    if zone == "PREMIUM":

        conflicts.append(
            "Preço em região Premium"
        )


    if module_score(
        modules,
        "timing",
    ) < 55:

        conflicts.append(
            "Timing sem confirmação forte"
        )


    return {

        "conflict_detected":
            len(conflicts) > 0,

        "conflicts":
            conflicts,

    }



# =====================================================
# ALINHAMENTO
# =====================================================

def calculate_alignment(
    conflicts: List[str],
):

    if len(conflicts) == 0:

        return "ALINHADO"


    if len(conflicts) >= 3:

        return "CONFLITANTE"


    return "PARCIAL"



# =====================================================
# ESTADO OPERACIONAL
# =====================================================

def calculate_decision_state(
    quality: float,
    conflict: bool,
):

    if quality < 50:

        return {

            "state":
                "BLOCKED",

            "color":
                "RED",

        }


    if conflict or quality < 75:

        return {

            "state":
                "WAIT_CONFIRMATION",

            "color":
                "YELLOW",

        }


    return {

        "state":
            "READY",

        "color":
            "GREEN",

    }



# =====================================================
# NÍVEL DE CONFIANÇA
# =====================================================

def calculate_confidence_level(
    quality: float,
):

    if quality >= 80:

        return "ALTA"


    if quality >= 55:

        return "MODERADA"


    return "BAIXA"



# =====================================================
# MENSAGEM PARA USUÁRIO
# =====================================================

def generate_user_message(
    state: str,
    conflicts: List[str],
    data: Dict[str, Any],
):

    direction = str(
        data.get(
            "direction",
            "NEUTRO",
        )
    ).upper()



    if state == "READY":

        return (
            f"Viés {direction} identificado. "
            "O cenário apresenta qualidade "
            "suficiente para acompanhamento "
            "da entrada."
        )



    if state == "WAIT_CONFIRMATION":

        if conflicts:

            return (
                f"Viés {direction} identificado, "
                "porém existem fatores de conflito. "
                "Aguardar confirmação antes da entrada."
            )


        return (
            "Oportunidade identificada. "
            "Aguardar confirmação do fluxo."
        )



    return (
        "A qualidade do cenário está abaixo "
        "do recomendado para operação."
    )



# =====================================================
# EXPLICAÇÃO
# =====================================================

def generate_ai_explanation(
    data: Dict[str, Any],
    conflicts: List[str],
):

    direction = str(
        data.get(
            "direction",
            "NEUTRO",
        )
    ).upper()



    if conflicts:

        return (
            f"O modelo identificou {direction}, "
            "porém existem conflitos reduzindo "
            "a qualidade da oportunidade."
        )


    return (
        f"O cenário apresenta alinhamento "
        f"favorável para {direction}."
    )



# =====================================================
# FATORES
# =====================================================

def positive_factors(
    data: Dict[str, Any],
):

    factors = []

    modules = data.get(
        "modules",
        {},
    )


    if module_score(
        modules,
        "technical",
    ) >= 70:

        factors.append(
            "Força técnica favorável"
        )


    if module_score(
        modules,
        "probabilistic",
    ) >= 60:

        factors.append(
            "Probabilidade aceitável"
        )


    return factors



def negative_factors(
    conflicts: List[str],
):

    return conflicts



# =====================================================
# FUNÇÃO PRINCIPAL
# =====================================================

def build_ai_brain(
    data: Dict[str, Any],
):

    ai_score = calculate_ai_score(
        data
    )


    trade_quality = calculate_trade_quality(
        data
    )


    conflict = detect_market_conflict(
        data
    )


    alignment = calculate_alignment(
        conflict["conflicts"]
    )


    decision = calculate_decision_state(
        trade_quality,
        conflict["conflict_detected"],
    )


    return {

        "ai_score":
            ai_score,


        "trade_quality_score":
            trade_quality,


        "signal_detected":
            data.get(
                "direction",
                "NEUTRO",
            ),


        "trading_action":
            (
                "AGUARDAR"
                if decision["state"] != "READY"
                else
                "MONITORAR ENTRADA"
            ),


        "entry_allowed":
            decision["state"]
            == "READY",


        "confidence_level":
            calculate_confidence_level(
                trade_quality
            ),


        "decision_state":
            decision["state"],


        "decision_color":
            decision["color"],


        "market_alignment":
            alignment,


        "conflict_detected":
            conflict[
                "conflict_detected"
            ],


        "ai_explanation":
            generate_ai_explanation(
                data,
                conflict["conflicts"],
            ),


        "user_message":
            generate_user_message(
                decision["state"],
                conflict["conflicts"],
                data,
            ),


        "positive_factors":
            positive_factors(
                data
            ),


        "negative_factors":
            negative_factors(
                conflict["conflicts"]
            ),


        "next_action":
            (
                "Aguardar confirmação do fluxo"
                if decision["state"] != "READY"
                else
                "Executar gestão da entrada"
            ),

    }