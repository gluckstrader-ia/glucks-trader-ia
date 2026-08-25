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
# SCORE PRINCIPAL
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
# QUALIDADE OPERACIONAL
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


    smc = module_score(
        modules,
        "smc",
    )

    probability = module_score(
        modules,
        "probabilistic",
    )


    if smc < 50:
        quality -= 10


    if probability < 55:
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


    market_context = data.get(
        "market_context",
        {},
    )


    technical = module_score(
        modules,
        "technical",
    )


    smc_bias = str(
        smc.get(
            "bias",
            "",
        )
    ).upper()


    zone = str(
        market_context.get(
            "zone_label",
            "",
        )
    ).upper()



    if direction == "COMPRA":

        if smc_bias in {
            "BEARISH",
            "BAIXA",
        }:
            conflicts.append(
                "SMC divergente da compra"
            )


    if direction == "VENDA":

        if smc_bias in {
            "BULLISH",
            "ALTA",
        }:
            conflicts.append(
                "SMC divergente da venda"
            )


    if zone == "PREMIUM":

        conflicts.append(
            "Preço em região Premium"
        )


    if technical < 60:

        conflicts.append(
            "Força técnica insuficiente"
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
    conflict_detected: bool,
    conflicts: List[str],
):

    if not conflict_detected:
        return "ALINHADO"


    if len(conflicts) >= 3:
        return "CONFLITANTE"


    return "PARCIAL"



# =====================================================
# EXPLICAÇÃO DA IA
# =====================================================

def generate_ai_explanation(
    data: Dict[str, Any],
    conflicts: List[str],
):

    direction = data.get(
        "direction",
        "NEUTRO",
    )


    if conflicts:

        return (
            f"O modelo identificou {direction}, "
            "porém existem conflitos que reduzem "
            "a qualidade da oportunidade."
        )


    return (
        f"O cenário apresenta alinhamento "
        f"favorável para {direction}."
    )



# =====================================================
# RECOMENDAÇÃO
# =====================================================

def generate_action(
    quality: float,
):

    if quality < 55:

        return {

            "trading_action":
                "AGUARDAR",

            "entry_allowed":
                False,

            "next_action":
                "Esperar confirmação do fluxo",

        }


    return {

        "trading_action":
            "MONITORAR ENTRADA",

        "entry_allowed":
            True,

        "next_action":
            "Acompanhar confirmação",

    }


# =====================================================
# FATORES
# =====================================================

def generate_positive_factors(
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



def generate_negative_factors(
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
        conflict["conflict_detected"],
        conflict["conflicts"],
    )


    action = generate_action(
        trade_quality
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
            action["trading_action"],


        "entry_allowed":
            action["entry_allowed"],


        "market_alignment":
            alignment,


        "conflict_detected":
            conflict["conflict_detected"],


        "ai_explanation":
            generate_ai_explanation(
                data,
                conflict["conflicts"],
            ),


        "positive_factors":
            generate_positive_factors(
                data
            ),


        "negative_factors":
            generate_negative_factors(
                conflict["conflicts"]
            ),


        "next_action":
            action["next_action"],

    }