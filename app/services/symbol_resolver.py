def normalize_asset(asset: str) -> str:
    return str(asset).upper().replace("/", "").replace(" ", "").strip()


def get_twelve_data_symbol(asset: str) -> str:
    asset = normalize_asset(asset)

    forex_pairs = {
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
        "USDCHF", "NZDUSD", "EURJPY", "GBPJPY", "EURGBP",
        "EURAUD", "EURCAD", "GBPCHF", "GBPAUD", "AUDJPY",
        "CADJPY", "CHFJPY", "AUDCAD", "AUDCHF", "NZDJPY",
        "XAUUSD", "USDBRL",
    }

    if asset in forex_pairs:
        return f"{asset[:3]}/{asset[3:]}"
    return asset


def get_yfinance_symbol(asset: str, asset_type: str) -> str:
    asset = normalize_asset(asset)
    asset_type = str(asset_type).lower().strip()

    # FOREX
    if asset_type == "forex":
        forex_map = {
            "XAUUSD": "GC=F",
            "USDBRL": "BRL=X",
        }
        return forex_map.get(asset, f"{asset}=X")

    # COMMODITIES
    if asset_type in {"commodity", "commodities"}:
        commodity_map = {
            "XAU": "GC=F",
            "XAUUSD": "GC=F",
            "XAG": "SI=F",
            "XAGUSD": "SI=F",
            "WTI": "CL=F",
            "BRENT": "BZ=F",
            "NG": "NG=F",
            "SOJA": "ZS=F",
            "MILHO": "ZC=F",
            "CAFE": "KC=F",
        }
        return commodity_map.get(asset, asset)

    # CRYPTO
    if asset_type == "crypto":
        if asset.endswith("USDT"):
            return f"{asset[:-4]}-USD"
        if asset.endswith("USD"):
            return f"{asset[:-3]}-USD"
        if asset.endswith("-USD"):
            return asset
        return f"{asset}-USD"

    # ÍNDICES
    if asset_type in {"index", "indices"}:
        index_map = {
            "SPX": "^GSPC",
            "SP500": "^GSPC",
            "S&P500": "^GSPC",
            "IBOV": "^BVSP",
            "IBOVESPA": "^BVSP",
            "NDX": "^NDX",
            "NASDAQ": "^IXIC",
            "DJI": "^DJI",
            "DOWJONES": "^DJI",
            "DAX": "^GDAXI",
            "JP225": "^N225",
            "NIKKEI": "^N225",
            "RUSSELL": "^RUT",
            "VIX": "^VIX",
        }
        return index_map.get(asset, asset)

    # B3
    if asset_type in {"b3", "acao_br", "acoes_br", "stock_br"}:
        if asset.endswith(".SA"):
            return asset
        return f"{asset}.SA"

    # AÇÕES EUA / GERAIS
    if asset_type in {"stock", "acoes", "acao"}:
        return asset

    # FUTUROS BR
    if asset_type in {"future_br", "futuro_br", "futuros_br"}:
        future_br_map = {
            "WIN": "^BVSP",
            "WINFUT": "^BVSP",
            "MINIINDICE": "^BVSP",
            "WDO": "BRL=X",
            "WDOFUT": "BRL=X",
            "MINIDOLAR": "BRL=X",
        }
        return future_br_map.get(asset, asset)

    # FUTUROS US
    if asset_type in {"future_us", "futuro_us", "futuros_us"}:
        future_us_map = {
            "NGCJ": "MGC=F",
            "MGC": "MGC=F",
            "MGC1!": "MGC=F",
            "MNQ": "NQ=F",
            "NQ": "NQ=F",
            "MNQ1!": "NQ=F",
            "ES": "ES=F",
            "ES1!": "ES=F",
            "CL": "CL=F",
            "CL1!": "CL=F",
            "GC": "GC=F",
            "GC1!": "GC=F",
        }
        return future_us_map.get(asset, asset)

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


def resolve_provider_symbol(asset: str, asset_type: str, provider: str = "yfinance") -> str:
    asset = normalize_asset(asset)
    asset_type = str(asset_type).lower().strip()
    provider = str(provider).lower().strip()

    if provider == "twelvedata":
        return get_twelve_data_symbol(asset)

    if provider == "yfinance":
        return get_yfinance_symbol(asset, asset_type)

    return asset