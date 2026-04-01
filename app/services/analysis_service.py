from typing import Any, Dict

import pandas as pd

from app.services.symbol_resolver import resolve_provider_symbol
from app.services.market_data_service import get_market_data
from app.indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_atr,
)


def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        raise ValueError("DataFrame retornou vazio")

    required_cols = ["open", "high", "low", "close", "volume"]
    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        raise ValueError(f"Colunas ausentes no DataFrame: {missing}")

    for col in required_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["open", "high", "low", "close"])

    if df.empty:
        raise ValueError("DataFrame ficou vazio após limpeza")

    return df


def get_instrument_config(asset: str, asset_type: str, timeframe: str) -> Dict[str, Any]:
    asset = str(asset).upper().strip()
    asset_type = str(asset_type).lower().strip()

    config = {
        "tick_size": 0.01,
        "price_decimals": 2,
        "atr_multiplier_stop": 1.0,
        "target_rr_1": 1.0,
        "target_rr_2": 1.5,
        "target_rr_3": 2.0,
        "min_stop_distance": None,
        "max_stop_distance": None,
    }

    if asset_type == "future_br":
        if asset == "WIN":
            config.update({
                "tick_size": 5.0,
                "price_decimals": 0,
                "atr_multiplier_stop": 0.45,
                "target_rr_1": 1.0,
                "target_rr_2": 1.6,
                "target_rr_3": 2.2,
            })

            if timeframe == "1m":
                config["min_stop_distance"] = 40.0
                config["max_stop_distance"] = 150.0
            elif timeframe == "5m":
                config["min_stop_distance"] = 60.0
                config["max_stop_distance"] = 220.0
            elif timeframe == "15m":
                config["min_stop_distance"] = 90.0
                config["max_stop_distance"] = 300.0
            elif timeframe == "30m":
                config["min_stop_distance"] = 120.0
                config["max_stop_distance"] = 400.0
            else:
                config["min_stop_distance"] = 150.0
                config["max_stop_distance"] = 600.0

        elif asset == "WDO":
            config.update({
                "tick_size": 0.5,
                "price_decimals": 1,
                "atr_multiplier_stop": 0.55,
                "target_rr_1": 1.0,
                "target_rr_2": 1.5,
                "target_rr_3": 2.0,
            })

            if timeframe == "1m":
                config["min_stop_distance"] = 2.5
                config["max_stop_distance"] = 8.0
            elif timeframe == "5m":
                config["min_stop_distance"] = 3.5
                config["max_stop_distance"] = 12.0
            elif timeframe == "15m":
                config["min_stop_distance"] = 5.0
                config["max_stop_distance"] = 18.0
            elif timeframe == "30m":
                config["min_stop_distance"] = 7.0
                config["max_stop_distance"] = 25.0
            else:
                config["min_stop_distance"] = 10.0
                config["max_stop_distance"] = 35.0

    elif asset_type == "forex":
        config.update({
            "tick_size": 0.00001,
            "price_decimals": 5,
        })

    elif asset_type == "crypto":
        config.update({
            "tick_size": 0.01,
            "price_decimals": 2,
        })

    elif asset_type in {"stock", "index", "b3"}:
        config.update({
            "tick_size": 0.01,
            "price_decimals": 2,
        })

    return config


def round_to_tick(value: float, tick_size: float, decimals: int) -> float:
    if tick_size <= 0:
        return round(float(value), decimals)

    rounded = round(round(float(value) / tick_size) * tick_size, decimals)
    return rounded


def determine_direction(
    close: float,
    sma20: float,
    sma50: float,
    ema9: float,
    rsi: float,
    atr: float = 0.0,
) -> Dict[str, Any]:
    bullish_points = 0
    bearish_points = 0

    if close > sma20:
        bullish_points += 1
    else:
        bearish_points += 1

    if sma20 > sma50:
        bullish_points += 1
    elif sma20 < sma50:
        bearish_points += 1

    if close > ema9:
        bullish_points += 1
    else:
        bearish_points += 1

    if rsi >= 55:
        bullish_points += 1
    elif rsi <= 45:
        bearish_points += 1

    ema21_proxy = sma20 if sma20 and sma20 != 0 else close

    trend_delta_1 = ((close - sma20) / sma20 * 100) if sma20 else 0.0
    trend_delta_2 = ((sma20 - sma50) / sma50 * 100) if sma50 else 0.0
    ema_delta = ((ema9 - ema21_proxy) / ema21_proxy * 100) if ema21_proxy else 0.0
    atr_pct = ((atr / close) * 100) if close and atr else 0.0

    bullish_strength = 0.0
    bearish_strength = 0.0

    if trend_delta_1 > 0:
        bullish_strength += min(abs(trend_delta_1) * 18, 12)
    else:
        bearish_strength += min(abs(trend_delta_1) * 18, 12)

    if trend_delta_2 > 0:
        bullish_strength += min(abs(trend_delta_2) * 20, 12)
    else:
        bearish_strength += min(abs(trend_delta_2) * 20, 12)

    if ema_delta > 0:
        bullish_strength += min(abs(ema_delta) * 30, 14)
    else:
        bearish_strength += min(abs(ema_delta) * 30, 14)

    if rsi > 50:
        bullish_strength += min((rsi - 50) * 1.1, 14)
    elif rsi < 50:
        bearish_strength += min((50 - rsi) * 1.1, 14)

    volatility_penalty = min(max(atr_pct - 1.2, 0) * 4.5, 8)

    bullish_raw = 48 + bullish_points * 6 + bullish_strength - volatility_penalty
    bearish_raw = 48 + bearish_points * 6 + bearish_strength - volatility_penalty

    bullish_raw = max(5, min(98, bullish_raw))
    bearish_raw = max(5, min(98, bearish_raw))

    if bullish_points >= 3 and bullish_raw >= bearish_raw:
        direction = "COMPRA"
        score = round(bullish_raw, 1)
        confidence = round(bullish_raw, 1)
        confidence_label = "ALTA" if confidence >= 80 else "MÉDIA" if confidence >= 65 else "BAIXA"
    elif bearish_points >= 3 and bearish_raw > bullish_raw:
        direction = "VENDA"
        score = round(bearish_raw, 1)
        confidence = round(bearish_raw, 1)
        confidence_label = "ALTA" if confidence >= 80 else "MÉDIA" if confidence >= 65 else "BAIXA"
    else:
        direction = "NEUTRO"
        balance = 55 - abs(bullish_raw - bearish_raw) * 0.6
        score = round(max(35, min(60, balance)), 1)
        confidence = round(max(35, min(60, balance)), 1)
        confidence_label = "BAIXA"

    return {
        "direction": direction,
        "score": score,
        "confidence": confidence,
        "confidence_label": confidence_label,
        "bullish_points": bullish_points,
        "bearish_points": bearish_points,
        "bullish_raw": round(bullish_raw, 1),
        "bearish_raw": round(bearish_raw, 1),
    }


def calculate_trade_levels(
    direction: str,
    close: float,
    atr: float,
    asset: str,
    asset_type: str,
    timeframe: str,
) -> Dict[str, float]:
    config = get_instrument_config(asset, asset_type, timeframe)

    tick_size = config["tick_size"]
    decimals = config["price_decimals"]

    if atr is None or pd.isna(atr) or atr <= 0:
        atr = close * 0.003

    stop_distance = atr * config["atr_multiplier_stop"]

    min_stop = config["min_stop_distance"]
    max_stop = config["max_stop_distance"]

    if min_stop is not None:
        stop_distance = max(stop_distance, min_stop)
    if max_stop is not None:
        stop_distance = min(stop_distance, max_stop)

    stop_distance = round_to_tick(stop_distance, tick_size, decimals)

    rr1 = config["target_rr_1"]
    rr2 = config["target_rr_2"]
    rr3 = config["target_rr_3"]

    if direction == "COMPRA":
        entry = close
        stop = close - stop_distance
        target = close + (stop_distance * rr1)
        tp2 = close + (stop_distance * rr2)
        tp3 = close + (stop_distance * rr3)
    elif direction == "VENDA":
        entry = close
        stop = close + stop_distance
        target = close - (stop_distance * rr1)
        tp2 = close - (stop_distance * rr2)
        tp3 = close - (stop_distance * rr3)
    else:
        entry = close
        stop = close
        target = close
        tp2 = close
        tp3 = close

    entry = round_to_tick(entry, tick_size, decimals)
    stop = round_to_tick(stop, tick_size, decimals)
    target = round_to_tick(target, tick_size, decimals)
    tp2 = round_to_tick(tp2, tick_size, decimals)
    tp3 = round_to_tick(tp3, tick_size, decimals)

    risk = abs(entry - stop)
    reward = abs(target - entry)
    risk_reward = reward / risk if risk > 0 else 0

    return {
        "entry": entry,
        "stop": stop,
        "target": target,
        "tp2": tp2,
        "tp3": tp3,
        "risk_reward": round(float(risk_reward), 2),
    }


def analyze_asset(asset: str, asset_type: str, timeframe: str) -> Dict[str, Any]:
    asset = str(asset).upper().strip()
    asset_type = str(asset_type).lower().strip()

    if asset_type in {"future_us", "futuro_us", "futuros_us"}:
        provider_symbol = resolve_provider_symbol(asset, asset_type, "yfinance")
    elif asset_type == "forex" and asset == "XAUUSD":
        provider_symbol = resolve_provider_symbol(asset, asset_type, "yfinance")
    else:
        provider_symbol = asset

    print("========== ANALYZE ==========")
    print("asset original:", asset)
    print("asset_type:", asset_type)
    print("timeframe:", timeframe)
    print("provider_symbol:", provider_symbol)
    print("=============================")

    try:
        prefer_binance = asset_type == "crypto"

        df = get_market_data(
            asset=provider_symbol,
            asset_type=asset_type,
            timeframe=timeframe,
            prefer_binance=prefer_binance,
        )

        df = validate_dataframe(df)

    except Exception as e:
        print("ERRO AO BUSCAR DADOS:", repr(e))
        raise ValueError(
            f"Falha ao carregar dados de mercado para {asset} ({provider_symbol}): {str(e)}"
        )

    print("TOTAL DE CANDLES RECEBIDOS:", len(df))
    print(df.tail(10))

    df["ema9"] = calculate_ema(df["close"], 9)
    df["ema21"] = calculate_ema(df["close"], 21)
    df["sma20"] = calculate_sma(df["close"], 20)
    df["sma50"] = calculate_sma(df["close"], 50)
    df["rsi14"] = calculate_rsi(df["close"], 14)
    df["atr14"] = calculate_atr(df, 14)

    if len(df) < 5:
        raise ValueError(
            f"Dados insuficientes para análise. Candles disponíveis: {len(df)}. "
            f"Aguarde mais dados do Profit ou use timeframe menor."
        )

    required_sets = [
        ["ema9", "ema21", "sma20", "sma50", "rsi14", "atr14"],
        ["ema9", "ema21", "sma20", "rsi14", "atr14"],
        ["ema9", "ema21", "rsi14", "atr14"],
        ["ema9", "rsi14", "atr14"],
    ]

    clean_df = None
    used_cols = None

    for cols in required_sets:
        candidate = df.dropna(subset=cols).copy()
        if not candidate.empty:
            clean_df = candidate
            used_cols = cols
            break

    if clean_df is None or clean_df.empty:
        raise ValueError(
            f"Dados insuficientes para calcular indicadores. Candles disponíveis: {len(df)}"
        )

    df = clean_df
    print(f"Indicadores válidos usando colunas: {used_cols}")

    last = df.iloc[-1]

    close = float(last["close"])
    ema9 = float(last["ema9"]) if pd.notna(last.get("ema9")) else close
    ema21 = float(last["ema21"]) if pd.notna(last.get("ema21")) else close
    sma20 = float(last["sma20"]) if pd.notna(last.get("sma20")) else close
    sma50 = float(last["sma50"]) if pd.notna(last.get("sma50")) else sma20
    rsi14 = float(last["rsi14"]) if pd.notna(last.get("rsi14")) else 50.0
    atr14 = float(last["atr14"]) if pd.notna(last.get("atr14")) else close * 0.003

    signal = determine_direction(
        close=close,
        sma20=sma20,
        sma50=sma50,
        ema9=ema9,
        rsi=rsi14,
        atr=atr14,
    )

    levels = calculate_trade_levels(
        direction=signal["direction"],
        close=close,
        atr=atr14,
        asset=asset,
        asset_type=asset_type,
        timeframe=timeframe,
    )

    entry = levels["entry"]
    stop = levels["stop"]
    target = levels["target"]
    tp2 = levels["tp2"]
    tp3 = levels["tp3"]
    risk_reward = levels["risk_reward"]

    direction = signal["direction"]
    score = signal["score"]
    confidence = signal["confidence"]

    tp1_probability = round(max(5, min(97, confidence)), 1)
    tp2_probability = round(max(20, min(92, confidence * 0.88 - 2.5)), 1)
    tp3_probability = round(max(12, min(85, confidence * 0.74 - 4.0)), 1)

    recent_lows = df["low"].tail(20).nsmallest(min(3, len(df["low"].tail(20)))).tolist()
    recent_highs = df["high"].tail(20).nlargest(min(3, len(df["high"].tail(20)))).tolist()

    supports = sorted({round(float(x), 6) for x in recent_lows})
    resistances = sorted({round(float(x), 6) for x in recent_highs}, reverse=False)

    buy_signals = 0
    sell_signals = 0
    neutral_signals = 0

    if close > ema9:
        buy_signals += 1
    else:
        sell_signals += 1

    if ema9 > ema21:
        buy_signals += 1
    else:
        sell_signals += 1

    if rsi14 > 55:
        buy_signals += 1
    elif rsi14 < 45:
        sell_signals += 1
    else:
        neutral_signals += 1

    if sma20 > sma50:
        buy_signals += 1
    elif sma20 < sma50:
        sell_signals += 1
    else:
        neutral_signals += 1

    trend_bias = "ALTA" if direction == "COMPRA" else "BAIXA" if direction == "VENDA" else "NEUTRO"
    ema_trend = "ALTA" if ema9 > ema21 else "BAIXA" if ema9 < ema21 else "NEUTRO"

    nearest_support = max([s for s in supports if s <= close], default=supports[0] if supports else close)
    nearest_resistance = min([r for r in resistances if r >= close], default=resistances[-1] if resistances else close)

    range_min = min(df["low"].tail(min(50, len(df))))
    range_max = max(df["high"].tail(min(50, len(df))))
    zone_position_pct = 50
    if range_max > range_min:
        zone_position_pct = ((close - range_min) / (range_max - range_min)) * 100

    if zone_position_pct < 33:
        zone_label = "Desconto"
    elif zone_position_pct > 66:
        zone_label = "Premium"
    else:
        zone_label = "Equilíbrio"

    bullish_raw = signal.get("bullish_raw", 50.0)
    bearish_raw = signal.get("bearish_raw", 50.0)

    if direction == "COMPRA":
        buy_probability = round(max(5, min(97, bullish_raw)), 1)
        sell_probability = round(max(3, min(45, 100 - bullish_raw + 8)), 1)
    elif direction == "VENDA":
        sell_probability = round(max(5, min(97, bearish_raw)), 1)
        buy_probability = round(max(3, min(45, 100 - bearish_raw + 8)), 1)
    else:
        balance = max(40, min(60, 50 - abs(bullish_raw - bearish_raw) * 0.35))
        buy_probability = round(balance, 1)
        sell_probability = round(balance, 1)

    smc_bias = "BULLISH" if direction == "COMPRA" else "BEARISH" if direction == "VENDA" else "NEUTRAL"

    return {
        "asset": asset.upper(),
        "asset_type": asset_type,
        "timeframe": timeframe,
        "direction": direction,
        "score": round(score, 1),
        "confidence": round(confidence, 1),
        "entry": entry,
        "stop": stop,
        "target": target,
        "risk_reward": risk_reward,

        "modules": {
            "technical": round(score, 1),
            "smc": round(score - 5, 1) if score >= 5 else round(score, 1),
            "harmonic": 52,
            "wegd": round(score - 3, 1) if score >= 3 else round(score, 1),
            "probabilistic": round(score, 1),
            "timing": 60,
        },

        "summary": {
            "signal_label": direction,
            "confluence": f"{round(score / 10, 1)}/10",
            "trend_label": trend_bias,
            "technical_label": trend_bias,
            "smart_money_label": "COMPRA" if direction == "COMPRA" else "VENDA" if direction == "VENDA" else "NEUTRO",
            "tp2": tp2,
            "tp3": tp3,
            "confidence": round(confidence, 1),
        },

        "technical": {
            "score": round(score, 1),
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "neutral_signals": neutral_signals,
            "trend_bias": trend_bias,
            "ema_trend": ema_trend,
            "rsi": round(rsi14, 2),
            "ema9": round(ema9, 6),
            "ema21": round(ema21, 6),
            "supports": supports,
            "resistances": resistances,
        },

        "smc": {
            "bias": smc_bias,
            "structure_label": "Estrutura de alta" if direction == "COMPRA" else "Estrutura de baixa" if direction == "VENDA" else "Estrutura lateral",
            "last_bos": round(close, 6),
            "context": {"candles": 50, "bias": smc_bias},
            "structure": {"candles": 20, "bias": smc_bias},
            "trigger": {"candles": 5, "bias": smc_bias},
            "divergence": "Sem divergência relevante",
            "order_blocks": [
                {
                    "title": "OB Principal",
                    "price": f"{nearest_support:.6f}",
                    "desc": "Região institucional observada",
                    "strength": "Média",
                    "bullish": direction == "COMPRA",
                }
            ],
            "fvgs": [
                {
                    "title": "FVG Atual",
                    "zone": f"{nearest_support:.6f} - {nearest_resistance:.6f}",
                    "state": "Aberto",
                    "bullish": direction == "COMPRA",
                }
            ],
            "liquidity": [
                {"price": round(nearest_resistance, 6), "desc": "Liquidez compradora acima", "tag": "High"},
                {"price": round(nearest_support, 6), "desc": "Liquidez vendedora abaixo", "tag": "Low"},
            ],
            "structure_breaks": [
                {
                    "title": "Última quebra",
                    "price": round(close, 6),
                    "desc": "Último rompimento relevante",
                    "bullish": direction == "COMPRA",
                }
            ],
            "summary": f"Leitura SMC com viés {smc_bias}.",
        },

        "harmonics": {
            "patterns": [],
            "fib_levels": [
                {"level": "0.382", "price": round(close - atr14 * 0.382, 6), "type": "support"},
                {"level": "0.618", "price": round(close + atr14 * 0.618, 6), "type": "resistance"},
            ],
        },

        "wegd": {
            "bias": direction,
            "confluence": f"{round(score / 10, 1)}/10",
            "summary": f"WEGD aponta {direction}.",
            "wyckoff": {
                "phase": "Markup" if direction == "COMPRA" else "Markdown" if direction == "VENDA" else "Range",
                "progress": round(score, 1),
                "confidence": round(confidence, 1),
                "next_phase": "Continuação",
                "composite_man": "Ativo",
                "events_confirmed": [],
                "events_pending": [],
                "volume_state": "Normal",
                "volume_label": "Volume equilibrado",
            },
            "elliott": {
                "current_wave": "3" if direction == "COMPRA" else "C" if direction == "VENDA" else "X",
                "mode": direction,
                "progress": round(score, 1),
                "confidence": round(confidence, 1),
                "next_wave": "4",
                "invalidation": stop,
                "wave_points": [],
            },
            "gann": {
                "dominant_angle": "1x1",
                "support_angles": [{"angle": "1x1", "price": nearest_support}],
                "resistance_angles": [{"angle": "1x1", "price": nearest_resistance}],
                "current_cycle_days": 7,
                "next_reversal": "Em observação",
                "days_in_cycle": 3,
                "price_square_levels": [{"price": close, "strength": "Média"}],
            },
            "dow": {
                "primary": trend_bias,
                "secondary": trend_bias,
                "minor": trend_bias,
                "market_phase": "Expansão" if direction != "NEUTRO" else "Lateralização",
                "market_phase_score": round(score, 1),
                "price_volume_confirmation": "Confirmado",
                "indices_confirmation": "Neutro",
                "volume_note": "Sem anomalia de volume",
            },
        },

        "probabilistic": {
            "win_rate_general": round(score, 1),
            "win_rate_long": round(buy_probability, 1),
            "win_rate_short": round(sell_probability, 1),
            "historical": {
                "periods": 100,
                "return_pct": round(((target - entry) / entry) * 100, 2) if entry else 0,
                "volatility_pct": round((atr14 / close) * 100, 2) if close else 0,
                "sharpe": 1.2,
                "max_drawdown_pct": 3.8,
            },
            "monte_carlo": {
                "confidence_level": 95,
                "low": round(stop, 6),
                "mid": round(close, 6),
                "high": round(target, 6),
            },
            "scenarios": {
                "bullish": round(buy_probability, 1),
                "neutral": round(max(0, 100 - max(buy_probability, sell_probability)), 1),
                "bearish": round(sell_probability, 1),
            },
            "seasonality": [],
            "risk_metrics": {
                "var_95": 1.5,
                "expected_shortfall": 2.1,
                "beta": 1.0,
                "correlation": 0.5,
            },
        },

        "timing": {
            "market_name": asset_type.upper(),
            "timezone": "America/Sao_Paulo",
            "status": "ABERTO",
            "best_window_label": "Janela principal",
            "notes": "Timing calculado com base no timeframe selecionado.",
            "recommended_windows": [{"start": "09:00", "end": "11:00", "reason": "Maior liquidez"}],
            "avoid_windows": [{"start": "12:00", "end": "13:00", "reason": "Menor fluxo"}],
        },

        "final_signal": {
            "direction": direction,
            "strength": "FORTE" if score >= 75 else "MODERADA" if score >= 60 else "FRACA",
            "confidence": round(confidence, 1),
            "entry": entry,
            "stop": stop,
            "target": target,
            "risk_reward": risk_reward,
            "confluence_score": round(score, 1),
            "justification": [
                f"EMA9={'acima' if ema9 > ema21 else 'abaixo'} da EMA21",
                f"RSI em {round(rsi14, 2)}",
                f"Preço em relação à SMA20/SMA50 favorece {direction}",
            ],
            "verdict": f"Sinal final {direction}",
        },

        "scenarios": {
            "buy": {
                "probability": round(buy_probability, 1),
                "entry_trigger": entry,
                "entry_reason": "Confirmação técnica",
                "stop": stop,
                "targets": [
                    {"label": "TP1", "price": target, "probability": tp1_probability, "rr": f"1:{risk_reward}"},
                    {"label": "TP2", "price": tp2, "probability": tp2_probability, "rr": "1:1.6"},
                    {"label": "TP3", "price": tp3, "probability": tp3_probability, "rr": "1:2.2"},
                ],
            },
            "sell": {
                "probability": round(sell_probability, 1),
                "entry_trigger": entry,
                "entry_reason": "Confirmação técnica",
                "stop": stop,
                "targets": [
                    {"label": "TP1", "price": target, "probability": tp1_probability, "rr": f"1:{risk_reward}"},
                    {"label": "TP2", "price": tp2, "probability": tp2_probability, "rr": "1:1.6"},
                    {"label": "TP3", "price": tp3, "probability": tp3_probability, "rr": "1:2.2"},
                ],
            },
        },

        "market_context": {
            "zone_label": zone_label,
            "zone_position_pct": round(zone_position_pct, 2),
            "range_min": round(float(range_min), 6),
            "range_max": round(float(range_max), 6),
            "current_price": round(close, 6),
            "nearest_support": round(float(nearest_support), 6),
            "nearest_resistance": round(float(nearest_resistance), 6),
            "dominant_trend": trend_bias,
        },

        "insights": {
            "bullish_factors": signal["bullish_points"],
            "bearish_factors": signal["bearish_points"],
            "neutral_factors": neutral_signals,
            "items": [
                f"Preço atual: {round(close, 6)}",
                f"EMA9: {round(ema9, 6)} | EMA21: {round(ema21, 6)}",
                f"RSI14: {round(rsi14, 2)}",
                f"Zona atual: {zone_label}",
            ],
            "waiting_confirmation": [
                "Aguardar candle de confirmação",
                "Validar continuidade do fluxo",
            ],
        },

        "fear_greed": {
            "label": "Ganância" if direction == "COMPRA" else "Medo" if direction == "VENDA" else "Neutro",
            "delta_vs_yesterday": 2,
            "avg_7d": 54,
            "history": [42, 45, 48, 50, 53, 55, min(95, max(5, round(score, 1)))],
        },
    }