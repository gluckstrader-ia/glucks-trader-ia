from typing import Any, Dict, List
from fastapi import APIRouter

from app.services.news_service import get_market_news, get_economic_events

router = APIRouter(prefix="", tags=["news"])


@router.get("/news")
def read_news():
    items = get_market_news()
    return {"items": items}


@router.get("/economic-events")
def read_economic_events():
    items = get_economic_events()
    return {"items": items}