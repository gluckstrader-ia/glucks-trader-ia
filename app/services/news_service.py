from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
import xml.etree.ElementTree as ET

import requests


DEFAULT_TIMEOUT = 12


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _infer_source_from_link(link: str) -> str:
    link = _safe_text(link)
    if "infomoney" in link.lower():
        return "infomoney.br"
    if "investing.com" in link.lower():
        return "investing.com"
    if "reuters" in link.lower():
        return "Reuters"
    if "bloomberg" in link.lower():
        return "Bloomberg"
    return "mercado"


def _format_pub_date(pub_date: str | None) -> str:
    if not pub_date:
        return "Agora há pouco"

    candidates = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
    ]

    for fmt in candidates:
        try:
            dt = datetime.strptime(pub_date, fmt)
            return dt.strftime("%H:%M")
        except Exception:
            continue

    return "Agora há pouco"


def get_market_news() -> List[Dict[str, Any]]:
    feeds = [
        "https://www.infomoney.com.br/feed/",
        "https://br.investing.com/rss/news_285.rss",
    ]

    items: List[Dict[str, Any]] = []

    for feed_url in feeds:
        try:
            response = requests.get(feed_url, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            channel = root.find("channel")
            if channel is None:
                continue

            for item in channel.findall("item")[:6]:
                title = _safe_text(item.findtext("title"), "Sem título")
                summary = _safe_text(item.findtext("description"), "Sem resumo disponível.")
                link = _safe_text(item.findtext("link"))
                pub_date = _safe_text(item.findtext("pubDate"))
                author = _safe_text(item.findtext("author"), "Redação")

                items.append(
                    {
                        "title": title,
                        "summary": summary,
                        "source": _infer_source_from_link(link),
                        "time": _format_pub_date(pub_date),
                        "author": author,
                        "highlight": len(items) == 0,
                        "url": link,
                    }
                )
        except Exception:
            continue

    if items:
        return items[:10]

    return [
        {
            "title": "Mercado em monitoramento",
            "summary": "Não foi possível atualizar as notícias externas no momento.",
            "source": "sistema",
            "time": "Agora há pouco",
            "author": "Gluck's Trader IA",
            "highlight": True,
            "url": "",
        }
    ]


def get_economic_events() -> List[Dict[str, Any]]:
    # fallback inicial
    # depois você pode trocar por API real (TradingEconomics, FMP, etc.)
    return [
        {
            "time": "09:00",
            "country": "🇧🇷 BR",
            "event": "IPCA-15",
            "actual": "0,38%",
            "forecast": "0,34%",
            "previous": "0,29%",
            "color": "bg-red-500",
        },
        {
            "time": "10:45",
            "country": "🇺🇸 US",
            "event": "PMI Industrial",
            "actual": "51,2",
            "forecast": "50,8",
            "previous": "50,1",
            "color": "bg-yellow-400",
        },
        {
            "time": "11:00",
            "country": "🇺🇸 US",
            "event": "Vendas de Casas Novas",
            "actual": "684K",
            "forecast": "676K",
            "previous": "662K",
            "color": "bg-yellow-400",
        },
        {
            "time": "15:00",
            "country": "🇺🇸 US",
            "event": "Discurso do Fed",
            "actual": "—",
            "forecast": "—",
            "previous": "—",
            "color": "bg-red-500",
        },
    ]