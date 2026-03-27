from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass
from datetime import datetime, date, time as dtime, timedelta
from pathlib import Path
from typing import Any, Optional

import pythoncom
import win32com.client


BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "profit_rtd_config.json"
FEED_FILE = BASE_DIR / "profit_feed.csv"


@dataclass
class CollectorConfig:
    workbook_name: str
    sheet_name: str
    start_row: int
    poll_interval_seconds: float
    columns: dict
    accepted_symbols: list[str]


def load_config() -> CollectorConfig:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    return CollectorConfig(
        workbook_name=raw["workbook_name"],
        sheet_name=raw["sheet_name"],
        start_row=int(raw.get("start_row", 2)),
        poll_interval_seconds=float(raw.get("poll_interval_seconds", 1.0)),
        columns=raw["columns"],
        accepted_symbols=[str(x).upper().strip() for x in raw.get("accepted_symbols", [])],
    )


def normalize_symbol(symbol: str) -> str:
    symbol = str(symbol).upper().strip().replace(" ", "")
    mapping = {
        "WINFUT": "WIN",
        "WDOFUT": "WDO",
        "WIN": "WIN",
        "WDO": "WDO",
    }
    return mapping.get(symbol, symbol)


def ensure_feed_file() -> None:
    if not FEED_FILE.exists():
        with open(FEED_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["datetime", "symbol", "open", "high", "low", "close", "volume"])


def excel_col_to_index(col: str) -> int:
    col = col.upper().strip()
    result = 0
    for ch in col:
        result = result * 26 + (ord(ch) - ord("A") + 1)
    return result


def get_cell(sheet: Any, row: int, col_letter: str) -> Any:
    return sheet.Cells(row, excel_col_to_index(col_letter)).Value


def find_open_workbook(excel: Any, workbook_name: str) -> Any:
    target = workbook_name.lower().strip()
    for wb in excel.Workbooks:
        if str(wb.Name).lower().strip() == target:
            return wb
    raise FileNotFoundError(f"Workbook '{workbook_name}' não está aberto no Excel.")


def parse_excel_date(value: Any) -> Optional[date]:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)):
        origin = datetime(1899, 12, 30)
        return (origin + timedelta(days=float(value))).date()

    text = str(value).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def parse_excel_time(value: Any) -> Optional[dtime]:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, dtime):
        return value
    if isinstance(value, (int, float)):
        total_seconds = round(float(value) * 86400)
        h = (total_seconds // 3600) % 24
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        return dtime(hour=h, minute=m, second=s)

    text = str(value).strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            pass
    return None


def parse_datetime(date_value: Any, time_value: Any) -> datetime:
    d = parse_excel_date(date_value)
    t = parse_excel_time(time_value)

    if d and t:
        return datetime.combine(d, t)
    if d:
        return datetime.combine(d, dtime.min)
    if t:
        return datetime.combine(datetime.now().date(), t)
    return datetime.now()


def to_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default

    try:
        return float(value)
    except Exception:
        pass

    try:
        text = str(value).strip()
        if "," in text and "." in text:
            text = text.replace(".", "").replace(",", ".")
        elif "," in text:
            text = text.replace(",", ".")
        return float(text)
    except Exception:
        return default


def read_sheet_rows(sheet: Any, cfg: CollectorConfig) -> list[dict]:
    rows = []
    row = cfg.start_row
    empty_streak = 0
    accepted = {normalize_symbol(x) for x in cfg.accepted_symbols}

    while empty_streak < 50:
        symbol_raw = get_cell(sheet, row, cfg.columns["symbol"])
        date_raw = get_cell(sheet, row, cfg.columns["date"])
        time_raw = get_cell(sheet, row, cfg.columns["time"])
        open_raw = get_cell(sheet, row, cfg.columns["open"])
        high_raw = get_cell(sheet, row, cfg.columns["high"])
        low_raw = get_cell(sheet, row, cfg.columns["low"])
        close_raw = get_cell(sheet, row, cfg.columns["close"])
        volume_raw = get_cell(sheet, row, cfg.columns["volume"])

        if all(x in (None, "") for x in [symbol_raw, date_raw, time_raw, open_raw, high_raw, low_raw, close_raw, volume_raw]):
            empty_streak += 1
            row += 1
            continue

        empty_streak = 0

        symbol = normalize_symbol(symbol_raw)
        if accepted and symbol not in accepted:
            row += 1
            continue

        dt = parse_datetime(date_raw, time_raw)
        open_ = to_float(open_raw, 0.0)
        high = to_float(high_raw, 0.0)
        low = to_float(low_raw, 0.0)
        close = to_float(close_raw, 0.0)
        volume = to_float(volume_raw, 0.0)

        if open_ > 0 and high > 0 and low > 0 and close > 0:
            rows.append({
                "datetime": dt.isoformat(),
                "symbol": symbol,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            })

        row += 1

    return rows


def rewrite_feed(rows: list[dict]) -> int:
    with open(FEED_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["datetime", "symbol", "open", "high", "low", "close", "volume"])

        seen = set()
        count = 0

        for item in sorted(rows, key=lambda x: (x["symbol"], x["datetime"])):
            key = (item["datetime"], item["symbol"])
            if key in seen:
                continue
            seen.add(key)

            writer.writerow([
                item["datetime"],
                item["symbol"],
                f"{float(item['open']):.5f}",
                f"{float(item['high']):.5f}",
                f"{float(item['low']):.5f}",
                f"{float(item['close']):.5f}",
                f"{float(item['volume']):.2f}",
            ])
            count += 1

    return count


def main():
    cfg = load_config()
    ensure_feed_file()

    print("=== PROFIT COLLECTOR ===")
    print(f"Workbook esperado: {cfg.workbook_name}")
    print(f"Aba esperada: {cfg.sheet_name}")
    print(f"Saída: {FEED_FILE}")

    while True:
        try:
            pythoncom.CoInitialize()
            excel = win32com.client.GetActiveObject("Excel.Application")
            wb = find_open_workbook(excel, cfg.workbook_name)
            sheet = wb.Worksheets(cfg.sheet_name)

            rows = read_sheet_rows(sheet, cfg)
            count = rewrite_feed(rows)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {count} candles sincronizados")

        except Exception as e:
            print(f"[ERRO] {e}")

        finally:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

        time.sleep(cfg.poll_interval_seconds)


if __name__ == "__main__":
    main()