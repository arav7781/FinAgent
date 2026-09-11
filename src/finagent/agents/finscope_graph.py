"""FinScope — the advisory router.

    START → classify_intent → one of five subagents → END

One classifier, five specialists. The split exists because the five questions a
retail investor asks need genuinely different behaviour: teaching wants patience
and a video link, news wants live data and no invention, portfolio advice wants
the user's risk profile *before* it says anything at all.

Keyword fast-paths run before the classifier model. They are free, they are
right about the obvious cases, and skipping a model call on "latest Apple news"
is the difference between a snappy reply and a visible pause.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from finagent.agents import prompts
from finagent.agents.tools import custom_yt_search
from finagent.services import market_data, runtime

logger = logging.getLogger(__name__)

MAX_DOCUMENT_CHARS = 8000
NEWS_ARTICLE_LIMIT = 6

INTENTS = ("education", "document", "market", "strategy", "news")
DEFAULT_INTENT = "education"

SUBAGENT_FOR_INTENT: dict[str, str] = {
    "education": "financial_educator",
    "document": "document_analyzer",
    "market": "market_researcher",
    "strategy": "portfolio_coach",
    "news": "news_reporter",
}

AGENT_DISPLAY_NAMES: dict[str, str] = {
    "education": "Financial Educator",
    "document": "Document Analyzer",
    "market": "Market Researcher",
    "strategy": "Portfolio Coach",
    "news": "News Reporter",
}

VIDEO_KEYWORDS = ("video", "youtube")
NEWS_KEYWORDS = (
    "news", "headline", "latest", "breaking", "updates",
    "what's happening", "whats happening",
)
DOCUMENT_KEYWORDS = ("document", "startup", "company", "analyze", "this")


class FinScopeState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    intent: str
    document_text: str
    user_profile: str


# ─── Session document store ───────────────────────────────────────────────────
# A chat session keeps the text of the document the user uploaded so follow-up
# questions ("what does it say about revenue?") resolve without a re-upload.

_session_documents: dict[str, str] = {}


def store_session_document(session_id: str, document_text: str) -> None:
    _session_documents[session_id] = document_text
    logger.info("Stored document context for session %s", session_id)


def get_session_document(session_id: str) -> str:
    return _session_documents.get(session_id, "")


def clear_session(session_id: str) -> None:
    _session_documents.pop(session_id, None)


# ─── Nodes ────────────────────────────────────────────────────────────────────

def _last_text(state: FinScopeState) -> str:
    messages = state["messages"]
    if not messages:
        return ""
    content = messages[-1].content
    return content if isinstance(content, str) else str(content)


def classify_intent(state: FinScopeState) -> dict:
    """Route the message to a subagent."""
    logger.info("--- FINSCOPE: CLASSIFY INTENT ---")
    text = _last_text(state).lower()

    if any(keyword in text for keyword in VIDEO_KEYWORDS):
        return {"intent": "education"}
    if any(keyword in text for keyword in NEWS_KEYWORDS):
        return {"intent": "news"}
    if state.get("document_text", "").strip() and any(
        keyword in text for keyword in DOCUMENT_KEYWORDS
    ):
        return {"intent": "document"}

    try:
        llm = runtime.build_llm(temperature=0.0, max_tokens=20)
        response = llm.invoke([
            SystemMessage(content=prompts.INTENT_CLASSIFIER),
            HumanMessage(content=_last_text(state)),
        ])
        intent = str(response.content).strip().lower().strip("\"'")
        if intent not in INTENTS:
            intent = DEFAULT_INTENT
    except Exception as exc:
        logger.warning("Intent classification failed (%s) — defaulting", exc)
        intent = DEFAULT_INTENT

    logger.info("Intent classified: %s", intent)
    return {"intent": intent}


def financial_educator(state: FinScopeState) -> dict:
    """Explain a concept, attaching real video results when asked for them."""
    logger.info("--- SUBAGENT: FINANCIAL EDUCATOR ---")
    text = _last_text(state)

    video_context = ""
    if any(keyword in text.lower() for keyword in VIDEO_KEYWORDS):
        logger.info("Video requested — searching YouTube")
        results = custom_yt_search.invoke(text)
        video_context = (
            f"\n\n=== YOUTUBE VIDEO RESULTS ===\n{results}\n==========================="
        )

    llm = runtime.build_llm(temperature=0.4, max_tokens=1800)
    response = llm.invoke(
        [SystemMessage(content=prompts.FINANCIAL_EDUCATOR + video_context)]
        + list(state["messages"])
    )
    return {"messages": [AIMessage(content=response.content)]}


def document_analyzer(state: FinScopeState) -> dict:
    """Summarise an uploaded document into the UI's flashcard format."""
    logger.info("--- SUBAGENT: DOCUMENT ANALYZER ---")
    document_text = state.get("document_text", "")
    system = prompts.DOCUMENT_ANALYZER + (
        f"\n\n=== DOCUMENT DATA ===\n{document_text[:MAX_DOCUMENT_CHARS]}"
        if document_text
        else "\n\nNo document has been uploaded yet."
    )

    llm = runtime.build_llm(temperature=0.2, max_tokens=2500)
    response = llm.invoke([SystemMessage(content=system)] + list(state["messages"]))
    return {"messages": [AIMessage(content=response.content)]}


def market_researcher(state: FinScopeState) -> dict:
    logger.info("--- SUBAGENT: MARKET RESEARCHER ---")
    llm = runtime.build_llm(temperature=0.3, max_tokens=2000)
    response = llm.invoke(
        [SystemMessage(content=prompts.MARKET_RESEARCHER)] + list(state["messages"])
    )
    return {"messages": [AIMessage(content=response.content)]}


def portfolio_coach(state: FinScopeState) -> dict:
    logger.info("--- SUBAGENT: PORTFOLIO COACH ---")
    llm = runtime.build_llm(temperature=0.3, max_tokens=2000)
    response = llm.invoke(
        [SystemMessage(content=prompts.PORTFOLIO_COACH)] + list(state["messages"])
    )
    return {"messages": [AIMessage(content=response.content)]}


def _format_news(articles: list) -> str:
    if not articles:
        return (
            "\n\nNo live news data available. Use your knowledge to provide "
            "general market context."
        )
    lines = ["\n\n=== LIVE NEWS DATA ==="]
    for item in articles:
        lines.append(
            f"\nTitle: {item.get('article_title', 'N/A')}"
            f"\n   Source: {item.get('source', 'N/A')}"
            f"\n   Time: {item.get('post_time_utc', 'N/A')}"
            f"\n   URL: {item.get('article_url', '')}"
            f"\n   Photo: {item.get('article_photo_url', '')}"
            f"\n   Snippet: {item.get('snippet', '')[:300]}"
            f"\n---"
        )
    lines.append("\n=== END NEWS DATA ===")
    return "".join(lines)


def news_reporter(state: FinScopeState) -> dict:
    """Fetch live articles first, then let the model summarise only those."""
    logger.info("--- SUBAGENT: NEWS REPORTER ---")
    symbol = market_data.resolve_symbol(_last_text(state))
    logger.info("Fetching news for %s", symbol)

    articles = market_data.fetch_news(symbol, limit=NEWS_ARTICLE_LIMIT)
    system = prompts.NEWS_REPORTER + _format_news(articles)

    llm = runtime.build_llm(temperature=0.3, max_tokens=2500)
    response = llm.invoke([SystemMessage(content=system)] + list(state["messages"]))
    return {"messages": [AIMessage(content=response.content)]}


def route_to_subagent(state: FinScopeState) -> str:
    return SUBAGENT_FOR_INTENT.get(state.get("intent", DEFAULT_INTENT), "financial_educator")


# ─── Graph ────────────────────────────────────────────────────────────────────

SUBAGENTS = {
    "financial_educator": financial_educator,
    "document_analyzer": document_analyzer,
    "market_researcher": market_researcher,
    "portfolio_coach": portfolio_coach,
    "news_reporter": news_reporter,
}


def build_graph():
    """Compile the FinScope router."""
    workflow = StateGraph(FinScopeState)
    workflow.add_node("classify_intent", classify_intent)
    for name, node in SUBAGENTS.items():
        workflow.add_node(name, node)

    workflow.add_edge(START, "classify_intent")
    workflow.add_conditional_edges(
        "classify_intent", route_to_subagent, {name: name for name in SUBAGENTS}
    )
    for name in SUBAGENTS:
        workflow.add_edge(name, END)

    return workflow.compile()


async def run_chat(
    question: str,
    user_profile: str = "beginner",
    document_text: str = "",
    session_id: str = "",
) -> dict[str, str]:
    """Answer one advisory message. Returns the answer plus routing metadata."""
    if not document_text and session_id:
        document_text = get_session_document(session_id)

    graph = build_graph()
    result = await graph.ainvoke(
        {
            "messages": [HumanMessage(content=question)],
            "intent": "",
            "document_text": document_text,
            "user_profile": user_profile,
        },
        {"recursion_limit": 10},
    )

    final = result["messages"][-1]
    intent = result.get("intent", DEFAULT_INTENT)
    return {
        "answer": final.content if isinstance(final.content, str) else str(final.content),
        "intent": intent,
        "agent": AGENT_DISPLAY_NAMES.get(intent, "Financial Educator"),
    }
