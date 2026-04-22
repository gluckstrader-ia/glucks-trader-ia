from typing import Dict


def build_initial_signal(market_state: Dict) -> Dict:
    asset = market_state["asset"]

    return {
        "signal": "wait",
        "confidence": 55,
        "entry": None,
        "stop": None,
        "target_1": None,
        "target_2": None,
        "risk_reward": None,
        "narration_text": (
            f"{asset} está em monitoramento na Sala ao Vivo IA. "
            "No momento, a leitura inicial é de observação, aguardando "
            "confirmações mais claras para compra ou venda."
        ),
    }