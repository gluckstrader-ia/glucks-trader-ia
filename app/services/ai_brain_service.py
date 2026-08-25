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
# CONFIANÇA DO SINAL
# =====================================================

def calculate_signal_confidence(
    data: Dict[str, Any],
):

    final_signal = data.get(
        "final_signal",
        {},
    )


    confidence = safe_float(
        final_signal.get(
            "confidence",
            50,
        )
    )


    if confidence >= 80:
        return "ALTA"


    if confidence >= 60:
        return "MODERADA"


    return "BAIXA"



# =====================================================
# QUALIDADE OPERACIONAL
# =====================================================

def calculate_trade_quality_label(
    quality: float,
):

    if quality >= 75:
        return "ALTA"


    if quality >= 55:
        return "MODERADA"


    return "BAIXA"



# =====================================================
# CONFLITOS REAIS
# =====================================================

def detect_market_conflicts(
    data: Dict[str, Any],
):

    conflicts = []


    direction = str(
        data.get(
            "direction",
            "NEUTRO",
        )
    ).upper()


    smc = data.get(
        "smc",
        {},
    )


    smc_bias = str(
        smc.get(
            "bias",
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



    return {

        "conflict_detected":
            len(conflicts) > 0,

        "conflicts":
            conflicts,

    }



# =====================================================
# ALERTAS OPERACIONAIS
# =====================================================

def detect_market_warnings(
    data: Dict[str, Any],
):

    warnings = []


    modules = data.get(
        "modules",
        {},
    )


    context = data.get(
        "market_context",
        {},
    )


    zone = str(
        context.get(
            "zone_label",
            "",
        )
    ).upper()



    if zone == "PREMIUM":

        warnings.append(
            "Preço em região Premium"
        )



    if zone == "DISCOUNT":

        warnings.append(
            "Preço em região Discount"
        )



    if module_score(
        modules,
        "timing",
    ) < 55:

        warnings.append(
            "Timing sem confirmação forte"
        )



    return {

        "warning_detected":
            len(warnings) > 0,

        "warnings":
            warnings,

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
# DECISÃO
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
# EXPLICAÇÕES
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
            "porém existem conflitos entre os módulos."
        )


    return (
        f"O cenário apresenta alinhamento "
        f"favorável para {direction}."
    )



def generate_user_message(
    state: str,
    warnings: List[str],
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
            "Cenário com qualidade operacional."
        )



    if state == "WAIT_CONFIRMATION":

        if conflicts:

            return (
                f"Viés {direction} identificado, "
                "porém existem conflitos entre modelos."
            )


        if warnings:

            return (
                f"Viés {direction} identificado, "
                "aguardar confirmação devido aos alertas."
            )



        return (
            "Aguardar confirmação do fluxo."
        )



    return (
        "Cenário abaixo do recomendado "
        "para operação."
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


    conflicts = detect_market_conflicts(
        data
    )


    warnings = detect_market_warnings(
        data
    )


    decision = calculate_decision_state(
        trade_quality,
        conflicts["conflict_detected"],
    )


    return {

        "ai_score":
            ai_score,


        "trade_quality_score":
            trade_quality,


        "trade_quality_label":
            calculate_trade_quality_label(
                trade_quality
            ),


        "signal_detected":
            data.get(
                "direction",
                "NEUTRO",
            ),


        "signal_confidence":
            calculate_signal_confidence(
                data
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


        "decision_state":
            decision["state"],


        "decision_color":
            decision["color"],


        "market_alignment":
            calculate_alignment(
                conflicts["conflicts"]
            ),


        "conflict_detected":
            conflicts["conflict_detected"],


        "conflicts":
            conflicts["conflicts"],


        "warning_detected":
            warnings["warning_detected"],


        "warnings":
            warnings["warnings"],


        "ai_explanation":
            generate_ai_explanation(
                data,
                conflicts["conflicts"],
            ),


        "user_message":
            generate_user_message(
                decision["state"],
                warnings["warnings"],
                conflicts["conflicts"],
                data,
            ),


        "positive_factors":
            positive_factors(
                data
            ),


        "negative_factors":
            (
                conflicts["conflicts"]
                +
                warnings["warnings"]
            ),


        "next_action":
            (
                "Aguardar confirmação do fluxo"
                if decision["state"] != "READY"
                else
                "Executar gestão da entrada"
            ),

    }