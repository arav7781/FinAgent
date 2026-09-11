"""Symbol resolution and the news cache."""

from dataclasses import replace

import pytest

from finagent.services import market_data


@pytest.mark.parametrize("query,expected", [
    ("Show me Apple news", "AAPL:NASDAQ"),
    ("what's happening with tesla", "TSLA:NASDAQ"),
    ("reliance latest", "RELIANCE:NSE"),
    ("infosys quarterly results", "INFY:NSE"),
    ("MSFT:NASDAQ", "MSFT:NASDAQ"),
])
def test_resolves_known_names_and_symbols(query, expected):
    assert market_data.resolve_symbol(query) == expected


def test_bare_ticker_defaults_to_nasdaq():
    assert market_data.resolve_symbol("SHOP") == "SHOP:NASDAQ"


def test_unresolvable_query_falls_back_to_default():
    assert market_data.resolve_symbol("!!!") == market_data.DEFAULT_SYMBOL
    assert market_data.resolve_symbol("") == market_data.DEFAULT_SYMBOL


def test_fetch_news_returns_empty_without_api_key():
    """No RAPIDAPI_KEY in the test environment, so no network call is made."""
    assert market_data.fetch_news("AAPL:NASDAQ") == []
    assert market_data.fetch_cash_flow("AAPL:NASDAQ") == []


def test_cache_serves_repeat_requests(monkeypatch):
    """A second read inside the TTL must not hit the provider again."""
    calls = {"count": 0}

    def fake_get(_path, _params):
        calls["count"] += 1
        return {"data": {"news": [{"article_title": "Headline"}]}}

    # Settings is frozen, so swap in a copy that has a key configured.
    monkeypatch.setattr(
        market_data, "settings", replace(market_data.settings, rapidapi_key="test")
    )
    monkeypatch.setattr(market_data, "_get", fake_get)
    market_data.clear_cache()

    first = market_data.fetch_news("AAPL:NASDAQ")
    second = market_data.fetch_news("AAPL:NASDAQ")

    assert first == second
    assert calls["count"] == 1, "second read should come from the cache"
    market_data.clear_cache()
