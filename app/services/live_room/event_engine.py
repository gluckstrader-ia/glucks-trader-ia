from typing import Dict, List


def build_initial_events(market_state: Dict) -> List[str]:
    asset = market_state["asset"]

    return [
        f"Sala ao Vivo IA iniciada para {asset}",
        "Aguardando leitura detalhada do mercado",
        "Estrutura inicial carregada com sucesso",
    ]