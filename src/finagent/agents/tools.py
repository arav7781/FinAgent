"""LangChain tools exposed to the agents.

Each tool's docstring is what the model sees when deciding whether to call it,
so the wording is part of the interface, not incidental documentation.
"""

from __future__ import annotations

import json
import logging

from langchain_core.tools import tool

from finagent.services import market_data, search

logger = logging.getLogger(__name__)


@tool
def search_market_data(query: str) -> str:
    """Search the web for market trends, competition, and industry data."""
    return search.web_search(query)


@tool
def finance_news_search(query: str) -> str:
    """Search for the latest financial news about a stock, company, or market topic.

    Input can be a company name like 'Apple' or a symbol like 'AAPL:NASDAQ'.
    """
    symbol = market_data.resolve_symbol(query)
    articles = market_data.fetch_news(symbol, limit=5)
    if not articles:
        return f"No news found for {symbol}."
    return "\n\n".join(
        f"{item.get('article_title', 'N/A')}\n"
        f"   Source: {item.get('source', 'N/A')} | {item.get('post_time_utc', '')}\n"
        f"   {item.get('snippet', '')[:200]}"
        for item in articles
    )


@tool
def finance_cash_flow(query: str) -> str:
    """Fetch quarterly cash flow data for a company.

    Input can be a company name like 'Apple' or a symbol like 'AAPL:NASDAQ'.
    """
    symbol = market_data.resolve_symbol(query)
    rows = market_data.fetch_cash_flow(symbol)
    if not rows:
        return f"No cash flow data found for {symbol}."
    return "\n\n".join(
        f"Date: {row.get('date', 'N/A')}\n"
        f"Operating Cash Flow: {row.get('operating_cash_flow', 'N/A')}\n"
        f"Free Cash Flow: {row.get('free_cash_flow', 'N/A')}"
        for row in rows
    )


@tool
def custom_yt_search(query: str) -> str:
    """Search for YouTube videos associated with a specific query or topic.

    The input should be a search string like 'startup basics'.
    """
    try:
        from youtube_search import YoutubeSearch

        term = query.split(",")[0] if "," in query else query
        payload = json.loads(YoutubeSearch(term, max_results=3).to_json())
        lines = [
            f"- **{video.get('title')}**: https://www.youtube.com{video.get('url_suffix')}"
            for video in payload.get("videos", [])
        ]
        return "\n".join(lines) if lines else "No videos found."
    except Exception as exc:
        logger.warning("YouTube search failed: %s", exc)
        return f"Error searching YouTube: {exc}"


# Tools bound to the evaluation analyst agent.
EVALUATION_TOOLS: list = [search_market_data]

# Tools available to the FinScope subagents.
FINSCOPE_TOOLS: list = [finance_news_search, finance_cash_flow, custom_yt_search]
