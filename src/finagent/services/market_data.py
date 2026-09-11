"""Live market data (RapidAPI real-time finance).

News is cached for five minutes per symbol. Financial news does not change
faster than that, and the cache keeps an interactive chat session well inside
free-tier request limits.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from finagent.settings import settings

logger = logging.getLogger(__name__)

# Common company names traders type instead of ticker symbols.
SYMBOL_ALIASES: dict[str, str] = {
    "apple": "AAPL:NASDAQ",
    "google": "GOOGL:NASDAQ",
    "alphabet": "GOOGL:NASDAQ",
    "microsoft": "MSFT:NASDAQ",
    "amazon": "AMZN:NASDAQ",
    "tesla": "TSLA:NASDAQ",
    "meta": "META:NASDAQ",
    "nvidia": "NVDA:NASDAQ",
    "netflix": "NFLX:NASDAQ",
    "reliance": "RELIANCE:NSE",
    "tcs": "TCS:NSE",
    "infosys": "INFY:NSE",
    "wipro": "WIPRO:NSE",
    "hdfc": "HDFCBANK:NSE",
    "icici": "ICICIBANK:NSE",
    "sbi": "SBIN:NSE",
}

DEFAULT_SYMBOL = "AAPL:NASDAQ"

_cache: dict[str, list[dict]] = {}
_cache_written_at: dict[str, float] = {}


def resolve_symbol(query: str) -> str:
    """Map free text to an ``EXCHANGE``-qualified symbol.

    Tries a known alias, then an explicit ``TICKER:EXCHANGE`` string, then a
    bare ticker assumed to be NASDAQ-listed.
    """
    text = (query or "").lower().strip()
    for alias, symbol in SYMBOL_ALIASES.items():
        if alias in text:
            return symbol

    if ":" in query:
        return query.strip()

    tokens = query.strip().split()
    if tokens:
        token = tokens[0].upper()
        if len(token) <= 5 and token.isalpha():
            return f"{token}:NASDAQ"
    return DEFAULT_SYMBOL


def _cached(key: str) -> list[dict] | None:
    age = time.time() - _cache_written_at.get(key, 0)
    if key in _cache and age < settings.news_cache_ttl_seconds:
        return _cache[key]
    return None


def _get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(
        f"{settings.rapidapi_base_url}{path}",
        headers={
            "X-RapidAPI-Key": settings.rapidapi_key,
            "X-RapidAPI-Host": settings.rapidapi_host,
        },
        params=params,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def fetch_news(symbol: str, limit: int = 5) -> list[dict]:
    """Latest articles for a symbol. Returns ``[]`` when data is unavailable."""
    if not settings.market_data_enabled:
        logger.warning("RAPIDAPI_KEY is not set — skipping news fetch")
        return []

    key = f"news_{symbol}"
    hit = _cached(key)
    if hit is not None:
        return hit[:limit]

    try:
        data = _get("/stock-news", {"symbol": symbol, "language": "en"})
        news = data.get("data", {}).get("news", [])
        _cache[key] = news
        _cache_written_at[key] = time.time()
        return news[:limit]
    except Exception as exc:
        logger.warning("News fetch failed for %s: %s", symbol, exc)
        return []


def fetch_cash_flow(symbol: str, quarters: int = 5) -> list[dict]:
    """Recent quarterly cash-flow rows. Returns ``[]`` when unavailable."""
    if not settings.market_data_enabled:
        logger.warning("RAPIDAPI_KEY is not set — skipping cash flow fetch")
        return []
    try:
        data = _get(
            "/company-cash-flow",
            {"symbol": symbol, "period": "QUARTERLY", "language": "en"},
        )
        return data.get("data", {}).get("cash_flow", [])[:quarters]
    except Exception as exc:
        logger.warning("Cash flow fetch failed for %s: %s", symbol, exc)
        return []


def clear_cache() -> None:
    _cache.clear()
    _cache_written_at.clear()
