"""Web search for market research.

Free search endpoints are unreliable, so three transports are tried in order
and the first usable answer wins. When all three fail the agent is told so
explicitly — that sentence lands in the prompt and the model falls back to its
own knowledge instead of silently inventing a citation.
"""

from __future__ import annotations

import logging
import re

import requests

logger = logging.getLogger(__name__)

MIN_RESULT_CHARS = 20
LITE_ENDPOINT = "https://lite.duckduckgo.com/lite/"
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

UNAVAILABLE_TEMPLATE = (
    "Web search unavailable. Using pre-trained knowledge for: {query}. "
    "Market analysis will be based on LLM knowledge up to the training cutoff."
)


def _via_search_run(query: str) -> str | None:
    from langchain_community.tools import DuckDuckGoSearchRun

    return DuckDuckGoSearchRun().run(query)


def _via_search_results(query: str) -> str | None:
    from langchain_community.tools import DuckDuckGoSearchResults

    return DuckDuckGoSearchResults(num_results=5).run(query)


def _via_lite_html(query: str) -> str | None:
    """Scrape the no-JavaScript endpoint when the library transports fail."""
    response = requests.post(
        LITE_ENDPOINT,
        data={"q": query},
        headers={"User-Agent": BROWSER_UA},
        timeout=8,
    )
    if response.status_code != 200 or len(response.text) < 100:
        return None
    text = re.sub(r"<[^>]+>", " ", response.text)
    return re.sub(r"\s{2,}", " ", text).strip()[:2000]


TRANSPORTS = [
    ("DuckDuckGoSearchRun", _via_search_run),
    ("DuckDuckGoSearchResults", _via_search_results),
    ("DuckDuckGo Lite", _via_lite_html),
]


def web_search(query: str) -> str:
    """Best-effort web search. Always returns a string the agent can read."""
    for name, transport in TRANSPORTS:
        try:
            result = transport(query)
        except Exception as exc:
            logger.warning("%s failed: %s", name, exc)
            continue
        if result and len(result.strip()) > MIN_RESULT_CHARS:
            logger.info("Web search succeeded via %s: %s", name, query[:60])
            return result

    logger.warning("All web search transports failed for: %s", query[:60])
    return UNAVAILABLE_TEMPLATE.format(query=query)
