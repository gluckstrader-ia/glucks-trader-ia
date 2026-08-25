from typing import Any, Dict, List


# =====================================================
# HELPERS
# =====================================================

def clamp(
    value: float,
    minimum: float = 0,
    maximum: float = 100,
):

    return max(
        minimum,
        min(maximum, value),
    )


def safe_float(
    value: Any,
    default: float = 50,
):

    try:
        return float(value)

    except Exception:
        return default



def module_score(
    modules: Dict[str, Any],
    key: str,
):

    return safe_float(
        modules.get(
            key,
            50,
        )
    )



# =====================================================
# SCORE PRINCIPAL
# =====================================================

def calculate_ai_score(
    data: Dict[str, Any],
):

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


    agreement = analyze_module_agreement(
        data
    )


    if agreement["module_alignment"] == "DIVERGENTE":

        score -= 10


    return round(
        clamp(score),
        1,
    )



# =====================================================
# QUALIDADE OPERACIONAL
# =====================================================

def calculate_trade_quality(
    data: Dict[str, Any],
):

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



    if strength == "FRACA":

        quality -= 15



    return round(
        clamp(quality),
        1,
    )



# =====================================================
# SIGNAL CONFIDENCE
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
# TRADE QUALITY LABEL
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
# MODULE AGREEMENT ENGINE
# =====================================================

def normalize_direction(
    value: Any,
):

    value = str(
        value or ""
    ).upper()


    if value in [
        "BUY",
        "COMPRA",
        "BULLISH",
        "ALTA",
    ]:
        return "COMPRA"


    if value in [
        "SELL",
        "VENDA",
        "BEARISH",
        "BAIXA",
    ]:
        return "VENDA"


    return "NEUTRO"



def analyze_module_agreement(
    data: Dict[str, Any],
):

    modules = data.get(
        "modules",
        {},
    )


    smc = data.get(
        "smc",
        {},
    )


    wegd = data.get(
        "wegd",
        {},
    )


    votes = {

        "technical":
            normalize_direction(
                modules.get(
                    "technical_direction"
                )
                or
                data.get(
                    "direction"
                )
            ),


        "smc":
            normalize_direction(
                smc.get(
                    "bias"
                )
            ),


        "wegd":
            normalize_direction(
                wegd.get(
                    "bias"
                )
            ),

    }


    directions = list(
        votes.values()
    )


    buy = directions.count(
        "COMPRA"
    )

    sell = directions.count(
        "VENDA"
    )

    neutral = directions.count(
        "NEUTRO"
    )


    score = max(
        buy,
        sell,
    ) / len(
        directions
    ) * 100



    conflicts = []


    if (
        buy > 0
        and sell > 0
    ):

        conflicts.append(
            "Módulos com direções opostas"
        )



    if (
        votes["technical"]
        != votes["wegd"]
        and
        votes["technical"] != "NEUTRO"
        and
        votes["wegd"] != "NEUTRO"
    ):

        conflicts.append(
            "Técnico divergente do WE/DG"
        )



    if buy == 3 or sell == 3:

        alignment = "ALINHADO"

    elif max(buy, sell) == 2 and neutral == 1:

        alignment = "PARCIAL"

    elif buy > 0 and sell > 0:

        alignment = "DIVERGENTE"

    else:

        alignment = "NEUTRO"



    return {

        "module_votes":
            votes,

        "module_alignment":
            alignment,

        "agreement_label":
            alignment,

        "module_agreement_score":
            round(
                score,
                1
            ),

        "module_conflicts":
            conflicts,

    }



# =====================================================
# CONFLITOS REAIS
# =====================================================

def detect_market_conflicts(
    data: Dict[str, Any],
):

    agreement = analyze_module_agreement(
        data
    )


    return {

        "conflict_detected":
            len(
                agreement["module_conflicts"]
            ) > 0,


        "conflicts":
            agreement["module_conflicts"],

    }



# =====================================================
# WARNINGS
# =====================================================

def detect_market_warnings(
    data: Dict[str, Any],
):

    warnings = []


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


    return {

        "warning_detected":
            len(warnings) > 0,

        "warnings":
            warnings,

    }



# =====================================================
# DECISION STATE
# =====================================================

def calculate_decision_state(
    quality: float,
    conflict: bool,
):

    if quality < 50:

        return {
            "state":"BLOCKED",
            "color":"RED"
        }



    if conflict or quality < 75:

        return {
            "state":"WAIT_CONFIRMATION",
            "color":"YELLOW"
        }



    return {
        "state":"READY",
        "color":"GREEN"
    }



# =====================================================
# MAIN
# =====================================================

def build_ai_brain(
    data: Dict[str, Any],
):

    agreement = analyze_module_agreement(
        data
    )


    conflicts = detect_market_conflicts(
        data
    )


    warnings = detect_market_warnings(
        data
    )


    quality = calculate_trade_quality(
        data
    )


    decision = calculate_decision_state(
        quality,
        conflicts["conflict_detected"],
    )


    return {

        "ai_score":
            calculate_ai_score(
                data
            ),


        "trade_quality_score":
            quality,


        "trade_quality_label":
            calculate_trade_quality_label(
                quality
            ),


        "signal_detected":
            data.get(
                "direction",
                "NEUTRO"
            ),


        "signal_confidence":
            calculate_signal_confidence(
                data
            ),


        "module_votes":
            agreement[
                "module_votes"
            ],


        "module_alignment":
            agreement[
                "module_alignment"
            ],


        "module_agreement_score":
            agreement[
                "module_agreement_score"
            ],


        "module_conflicts":
            agreement[
                "module_conflicts"
            ],


        "conflict_detected":
            conflicts[
                "conflict_detected"
            ],


        "conflicts":
            conflicts[
                "conflicts"
            ],


        "warning_detected":
            warnings[
                "warning_detected"
            ],


        "warnings":
            warnings[
                "warnings"
            ],


        "trading_action":
            (
                "AGUARDAR"
                if decision["state"]
                != "READY"
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

        "agreement_label":
            agreement[
                "agreement_label"
            ],

    }