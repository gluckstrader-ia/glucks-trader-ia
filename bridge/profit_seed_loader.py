from __future__ import annotations

import csv
from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
RAW_HISTORY_FILE = BASE_DIR / "profit_export_raw.csv"
NORMALIZED_HISTORY_FILE = BASE_DIR / "profit_history.csv"


def normalize_symbol(symbol: str) -> str:
    symbol = str(symbol).upper().strip().replace(" ", "")
    mapping = {
        "WINFUT": "WIN",
        "WDOFUT": "WDO",
        "MINIINDICE": "WIN",
        "MINIDOLAR": "WDO",
        "WIN": "WIN",
        "WDO": "WDO",
    }
    return mapping.get(symbol, symbol)


def normalize_number(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return float(text)
    except Exception:
        return None


def main():
    if not RAW_HISTORY_FILE.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {RAW_HISTORY_FILE}\n"
            f"Exporte o histórico do Profit para esse arquivo."
        )

    df = pd.read_csv(RAW_HISTORY_FILE)

    # Ajuste aqui se os nomes exportados pelo Profit forem diferentes
    rename_map = {
        "symbol": "symbol",
        "ativo": "symbol",
        "date": "date",
        "data": "date",
        "time": "time",
        "hora": "time",
        "open": "open",
        "abertura": "open",
        "high": "high",
        "maxima": "high",
        "máxima": "high",
        "low": "low",
        "minima": "low",
        "mínima": "low",
        "close": "close",
        "fechamento": "close",
        "volume": "volume",
    }

    df.columns = [rename_map.get(str(c).strip().lower(), str(c).strip().lower()) for c in df.columns]

    required = ["symbol", "date", "time", "open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes no histórico exportado: {missing}")

    df["symbol"] = df["symbol"].apply(normalize_symbol)
    df["datetime"] = pd.to_datetime(
        df["date"].astype(str).str.strip() + " " + df["time"].astype(str).str.strip(),
        errors="coerce"
    )

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].apply(normalize_number)

    df = df.dropna(subset=["datetime", "symbol", "open", "high", "low", "close"])
    df = df[["datetime", "symbol", "open", "high", "low", "close", "volume"]].copy()
    df = df.sort_values(["symbol", "datetime"])

    df.to_csv(NORMALIZED_HISTORY_FILE, index=False)
    print(f"Histórico normalizado salvo em: {NORMALIZED_HISTORY_FILE}")
    print(df.tail(10))


if __name__ == "__main__":
    main()