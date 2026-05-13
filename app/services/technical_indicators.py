from typing import Optional
import pandas as pd


def safe_float(value) -> Optional[float]:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def round_value(value, digits: int = 4):
    value = safe_float(value)
    return round(value, digits) if value is not None else None


def action_color_rule(action: str) -> str:
    return action


def rsi_action(value: Optional[float]) -> str:
    if value is None:
        return "—"
    if value >= 70:
        return "Sobrecompra"
    if value <= 30:
        return "Sobrevenda"
    if value >= 55:
        return "Compra"
    if value <= 45:
        return "Venda"
    return "Neutro"


def stochastic_action(value: Optional[float]) -> str:
    if value is None:
        return "—"
    if value >= 80:
        return "Sobrecompra"
    if value <= 20:
        return "Sobrevenda"
    if value >= 55:
        return "Compra"
    if value <= 45:
        return "Venda"
    return "Neutro"


def macd_action(macd: Optional[float], signal: Optional[float]) -> str:
    if macd is None or signal is None:
        return "—"
    if macd > signal:
        return "Compra"
    if macd < signal:
        return "Venda"
    return "Neutro"


def adx_action(adx: Optional[float], plus_di: Optional[float], minus_di: Optional[float]) -> str:
    if adx is None or plus_di is None or minus_di is None:
        return "—"

    if adx < 20:
        return "Neutro"

    if plus_di > minus_di:
        return "Compra"

    if minus_di > plus_di:
        return "Venda"

    return "Neutro"


def williams_action(value: Optional[float]) -> str:
    if value is None:
        return "—"
    if value >= -20:
        return "Sobrecompra"
    if value <= -80:
        return "Sobrevenda"
    if value > -50:
        return "Compra"
    if value < -50:
        return "Venda"
    return "Neutro"


def cci_action(value: Optional[float]) -> str:
    if value is None:
        return "—"
    if value >= 100:
        return "Compra"
    if value <= -100:
        return "Venda"
    return "Neutro"


def roc_action(value: Optional[float]) -> str:
    if value is None:
        return "—"
    if value > 0:
        return "Compra"
    if value < 0:
        return "Venda"
    return "Neutro"


def bull_bear_action(value: Optional[float]) -> str:
    if value is None:
        return "—"
    if value > 0:
        return "Compra"
    if value < 0:
        return "Venda"
    return "Neutro"


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()

    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))

    return rsi.fillna(50)


def calculate_stochastic(df: pd.DataFrame, k_period: int = 9, d_period: int = 6) -> pd.Series:
    low_min = df["low"].rolling(k_period).min()
    high_max = df["high"].rolling(k_period).max()

    k = 100 * ((df["close"] - low_min) / (high_max - low_min).replace(0, pd.NA))
    d = k.rolling(d_period).mean()

    return d


def calculate_stoch_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    rsi = calculate_rsi(close, period)

    min_rsi = rsi.rolling(period).min()
    max_rsi = rsi.rolling(period).max()

    stoch_rsi = 100 * ((rsi - min_rsi) / (max_rsi - min_rsi).replace(0, pd.NA))

    return stoch_rsi


def calculate_macd(close: pd.Series):
    ema12 = calculate_ema(close, 12)
    ema26 = calculate_ema(close, 26)

    macd = ema12 - ema26
    signal = calculate_ema(macd, 9)

    return macd, signal


def calculate_adx(df: pd.DataFrame, period: int = 14):
    high = df["high"]
    low = df["low"]
    close = df["close"]

    plus_dm = high.diff()
    minus_dm = low.diff() * -1

    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()

    plus_di = 100 * (plus_dm.rolling(period).mean() / atr.replace(0, pd.NA))
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr.replace(0, pd.NA))

    dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, pd.NA))
    adx = dx.rolling(period).mean()

    return adx, plus_di, minus_di


def calculate_williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
    highest_high = df["high"].rolling(period).max()
    lowest_low = df["low"].rolling(period).min()

    wr = -100 * ((highest_high - df["close"]) / (highest_high - lowest_low).replace(0, pd.NA))

    return wr


def calculate_cci(df: pd.DataFrame, period: int = 14) -> pd.Series:
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    sma = typical_price.rolling(period).mean()
    mean_deviation = (typical_price - sma).abs().rolling(period).mean()

    cci = (typical_price - sma) / (0.015 * mean_deviation.replace(0, pd.NA))

    return cci


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    return tr.rolling(period).mean()


def calculate_highs_lows(df: pd.DataFrame, period: int = 14) -> pd.Series:
    highest = df["high"].rolling(period).max()
    lowest = df["low"].rolling(period).min()

    midpoint = (highest + lowest) / 2

    return df["close"] - midpoint


def calculate_ultimate_oscillator(df: pd.DataFrame) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]

    prev_close = close.shift(1)

    bp = close - pd.concat([low, prev_close], axis=1).min(axis=1)
    tr = pd.concat([high, prev_close], axis=1).max(axis=1) - pd.concat([low, prev_close], axis=1).min(axis=1)

    avg7 = bp.rolling(7).sum() / tr.rolling(7).sum().replace(0, pd.NA)
    avg14 = bp.rolling(14).sum() / tr.rolling(14).sum().replace(0, pd.NA)
    avg28 = bp.rolling(28).sum() / tr.rolling(28).sum().replace(0, pd.NA)

    uo = 100 * ((4 * avg7) + (2 * avg14) + avg28) / 7

    return uo


def calculate_roc(close: pd.Series, period: int = 12) -> pd.Series:
    return ((close - close.shift(period)) / close.shift(period).replace(0, pd.NA)) * 100


def calculate_bull_bear_power(df: pd.DataFrame, period: int = 13) -> pd.Series:
    ema = calculate_ema(df["close"], period)

    bull_power = df["high"] - ema
    bear_power = df["low"] - ema

    return bull_power + bear_power


def atr_action(atr: Optional[float], close: Optional[float]) -> str:
    if atr is None or close is None or close == 0:
        return "—"

    atr_pct = (atr / close) * 100

    if atr_pct >= 0.15:
        return "Mais Volatilidade"

    if atr_pct <= 0.05:
        return "Baixa Volatilidade"

    return "Neutro"


def build_technical_indicators(df: pd.DataFrame) -> list[dict]:
    if df is None or df.empty:
        return []

    data = df.copy()

    for col in ["open", "high", "low", "close", "volume"]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.dropna(subset=["high", "low", "close"])

    if data.empty:
        return []

    close = data["close"]

    data["rsi14_calc"] = calculate_rsi(close, 14)
    data["stoch_9_6"] = calculate_stochastic(data, 9, 6)
    data["stochrsi14"] = calculate_stoch_rsi(close, 14)

    macd, macd_signal = calculate_macd(close)
    data["macd_12_26"] = macd
    data["macd_signal"] = macd_signal

    adx, plus_di, minus_di = calculate_adx(data, 14)
    data["adx14"] = adx
    data["plus_di14"] = plus_di
    data["minus_di14"] = minus_di

    data["williams_r14"] = calculate_williams_r(data, 14)
    data["cci14"] = calculate_cci(data, 14)
    data["atr14_calc"] = calculate_atr(data, 14)
    data["highs_lows14"] = calculate_highs_lows(data, 14)
    data["ultimate_oscillator"] = calculate_ultimate_oscillator(data)
    data["roc12"] = calculate_roc(close, 12)
    data["bull_bear_power13"] = calculate_bull_bear_power(data, 13)

    last = data.iloc[-1]

    rsi = safe_float(last.get("rsi14_calc"))
    stoch = safe_float(last.get("stoch_9_6"))
    stoch_rsi = safe_float(last.get("stochrsi14"))
    macd_value = safe_float(last.get("macd_12_26"))
    macd_signal_value = safe_float(last.get("macd_signal"))
    adx_value = safe_float(last.get("adx14"))
    plus_di_value = safe_float(last.get("plus_di14"))
    minus_di_value = safe_float(last.get("minus_di14"))
    williams_value = safe_float(last.get("williams_r14"))
    cci_value = safe_float(last.get("cci14"))
    atr_value = safe_float(last.get("atr14_calc"))
    close_value = safe_float(last.get("close"))
    highs_lows_value = safe_float(last.get("highs_lows14"))
    ultimate_value = safe_float(last.get("ultimate_oscillator"))
    roc_value = safe_float(last.get("roc12"))
    bull_bear_value = safe_float(last.get("bull_bear_power13"))

    indicators = [
        {
            "name": "RSI(14)",
            "value": round_value(rsi, 3),
            "action": rsi_action(rsi),
        },
        {
            "name": "STOCH(9,6)",
            "value": round_value(stoch, 3),
            "action": stochastic_action(stoch),
        },
        {
            "name": "STOCHRSI(14)",
            "value": round_value(stoch_rsi, 3),
            "action": stochastic_action(stoch_rsi),
        },
        {
            "name": "MACD(12,26)",
            "value": round_value(macd_value, 6),
            "action": macd_action(macd_value, macd_signal_value),
        },
        {
            "name": "ADX(14)",
            "value": round_value(adx_value, 3),
            "action": adx_action(adx_value, plus_di_value, minus_di_value),
        },
        {
            "name": "Williams %R",
            "value": round_value(williams_value, 3),
            "action": williams_action(williams_value),
        },
        {
            "name": "CCI(14)",
            "value": round_value(cci_value, 3),
            "action": cci_action(cci_value),
        },
        {
            "name": "ATR(14)",
            "value": round_value(atr_value, 6),
            "action": atr_action(atr_value, close_value),
        },
        {
            "name": "Highs/Lows(14)",
            "value": round_value(highs_lows_value, 6),
            "action": roc_action(highs_lows_value),
        },
        {
            "name": "Ultimate Oscillator",
            "value": round_value(ultimate_value, 3),
            "action": rsi_action(ultimate_value),
        },
        {
            "name": "ROC",
            "value": round_value(roc_value, 3),
            "action": roc_action(roc_value),
        },
        {
            "name": "Bull/Bear Power(13)",
            "value": round_value(bull_bear_value, 6),
            "action": bull_bear_action(bull_bear_value),
        },
    ]

    return indicators