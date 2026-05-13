from typing import Optional


def calculate_sma(values: list[float], period: int) -> Optional[float]:
    if len(values) < period:
        return None

    return sum(values[-period:]) / period


def calculate_ema(values: list[float], period: int) -> Optional[float]:
    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)

    ema = sum(values[:period]) / period

    for price in values[period:]:
        ema = (price - ema) * multiplier + ema

    return ema


def get_ma_action(current_price: float, ma_value: Optional[float]) -> str:
    if ma_value is None:
        return "—"

    if current_price > ma_value:
        return "Compra"

    if current_price < ma_value:
        return "Venda"

    return "Neutro"


def build_moving_averages(closes: list[float]) -> list[dict]:
    periods = [5, 10, 20, 50, 100, 200]

    clean_closes = []

    for price in closes:
        try:
            if price is not None:
                clean_closes.append(float(price))
        except Exception:
            continue

    if not clean_closes:
        return []

    current_price = clean_closes[-1]

    moving_averages = []

    for period in periods:
        sma = calculate_sma(clean_closes, period)
        ema = calculate_ema(clean_closes, period)

        moving_averages.append(
            {
                "name": f"MA{period}",
                "simple": round(sma, 6) if sma is not None else None,
                "simple_action": get_ma_action(current_price, sma),
                "exponential": round(ema, 6) if ema is not None else None,
                "exponential_action": get_ma_action(current_price, ema),
            }
        )

    return moving_averages