def normalize_asset(asset: str) -> str:
    return str(asset).upper().replace("/", "").replace(" ", "").strip()


def get_twelve_data_symbol(asset: str) -> str:
    asset = normalize_asset(asset)

    forex_pairs = {
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
        "USDCHF", "NZDUSD", "EURJPY", "GBPJPY", "EURGBP",
        "EURAUD", "EURCAD", "GBPCHF", "GBPAUD", "AUDJPY",
        "CADJPY", "CHFJPY", "AUDCAD", "AUDCHF", "NZDJPY"
    }

    if asset in forex_pairs:
        return f"{asset[:3]}/{asset[3:]}"
    return asset


def get_yfinance_symbol(asset: str, asset_type: str) -> str:
    asset = normalize_asset(asset)
    asset_type = str(asset_type).lower().strip()

    if asset_type == "forex":
        return f"{asset}=X"

    if asset_type == "crypto":
        if asset.endswith("USDT"):
            return f"{asset[:-4]}-USD"
        if asset.endswith("USD"):
            return f"{asset[:-3]}-USD"
        if asset.endswith("-USD"):
            return asset
        return f"{asset}-USD"

    if asset_type in {"index", "indices"}:
        index_map = {
            "SPX": "^GSPC",
            "SP500": "^GSPC",
            "S&P500": "^GSPC",
            "NASDAQ": "^IXIC",
            "NDX": "^NDX",
            "DJI": "^DJI",
            "DOWJONES": "^DJI",
            "RUSSELL": "^RUT",
            "VIX": "^VIX",
            "IBOV": "^BVSP",
            "IBOVESPA": "^BVSP",
        }
        return index_map.get(asset, asset)

    if asset_type in {"b3", "acao_br", "acoes_br", "stock_br"}:
        if asset.endswith(".SA"):
            return asset
        return f"{asset}.SA"

    if asset_type in {"stock", "acoes", "acao"}:
        return asset

    return asset


def get_br_futures_symbol(asset: str) -> str:
    asset = normalize_asset(asset)

    futures_map = {
        "WIN": "WIN",
        "WINFUT": "WIN",
        "MINIINDICE": "WIN",
        "WDO": "WDO",
        "WDOFUT": "WDO",
        "MINIDOLAR": "WDO",
    }

    return futures_map.get(asset, asset)