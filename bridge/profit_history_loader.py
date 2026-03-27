from __future__ import annotations

from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
RAW_FILE = BASE_DIR / "profit_export_raw.csv"
OUT_FILE = BASE_DIR / "profit_history.csv"


def normalize_symbol(symbol: str) -> str:
    symbol = str(symbol).upper().strip().replace(" ", "")
    mapping = {
        "WINFUT": "WIN",
        "WDOFUT": "WDO",
        "WIN": "WIN",
        "WDO": "WDO",
    }
    return mapping.get(symbol, symbol)


def normalize_price(value):
    """
    Preços do Profit no seu CSV vêm assim:
    186.610 -> 186610
    186.650 -> 186650
    """
    if pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    # remove separador de milhar
    text = text.replace(".", "").replace(",", ".")

    try:
        return float(text)
    except Exception:
        return None


def normalize_volume(value):
    """
    Volume do Profit no seu CSV vem assim:
    728.898.598,00 -> 728898598.00
    """
    if pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    text = text.replace(".", "").replace(",", ".")

    try:
        return float(text)
    except Exception:
        return None


def find_col(columns_map: dict, *candidates: str):
    for candidate in candidates:
        if candidate in columns_map:
            return columns_map[candidate]
    return None


def main():
    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {RAW_FILE}\n"
            f"Exporte o histórico do Profit para esse caminho."
        )

    # Seu arquivo usa ';'
    df = pd.read_csv(RAW_FILE, sep=";", encoding="latin-1")

    # mapa lowercase -> nome real da coluna
    normalized_cols = {}
    for c in df.columns:
        key = str(c).strip().lower()
        key = key.replace("á", "a").replace("à", "a").replace("â", "a").replace("ã", "a")
        key = key.replace("é", "e").replace("ê", "e")
        key = key.replace("í", "i")
        key = key.replace("ó", "o").replace("ô", "o").replace("õ", "o")
        key = key.replace("ú", "u")
        key = key.replace("ç", "c")
        key = key.replace("�", "")  # corrige cabeçalhos com encoding quebrado
        normalized_cols[key] = c

    symbol_col = find_col(normalized_cols, "ativo", "symbol")
    date_col = find_col(normalized_cols, "data", "date")
    time_col = find_col(normalized_cols, "hora", "time")
    open_col = find_col(normalized_cols, "abertura", "open")
    high_col = find_col(normalized_cols, "maximo", "máximo", "high")
    low_col = find_col(normalized_cols, "minimo", "mínimo", "low")
    close_col = find_col(normalized_cols, "fechamento", "close")
    volume_col = find_col(normalized_cols, "volume", "vol")
    qty_col = find_col(normalized_cols, "quantidade", "qty", "trades")

    required = [symbol_col, date_col, time_col, open_col, high_col, low_col, close_col, volume_col]
    if any(c is None for c in required):
        raise ValueError(
            "Não foi possível identificar todas as colunas obrigatórias no profit_export_raw.csv.\n"
            f"Colunas encontradas: {list(df.columns)}"
        )

    out = pd.DataFrame()
    out["symbol"] = df[symbol_col].apply(normalize_symbol)
    out["datetime"] = pd.to_datetime(
        df[date_col].astype(str).str.strip() + " " + df[time_col].astype(str).str.strip(),
        format="%d/%m/%Y %H:%M:%S",
        errors="coerce"
    )

    out["open"] = df[open_col].apply(normalize_price)
    out["high"] = df[high_col].apply(normalize_price)
    out["low"] = df[low_col].apply(normalize_price)
    out["close"] = df[close_col].apply(normalize_price)
    out["volume"] = df[volume_col].apply(normalize_volume)

    # quantidade é opcional; pode ser útil depois
    if qty_col is not None:
        out["trades"] = df[qty_col].apply(normalize_volume)

    out = out.dropna(subset=["datetime", "symbol", "open", "high", "low", "close"])
    out = out.sort_values(["symbol", "datetime"])

    # mantém só o que a bridge precisa
    out = out[["datetime", "symbol", "open", "high", "low", "close", "volume"]]

    out.to_csv(OUT_FILE, index=False)
    print(f"Histórico normalizado salvo em: {OUT_FILE}")
    print(out.tail(10))


if __name__ == "__main__":
    main()