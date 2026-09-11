"""The startup evaluation workflow.

    START → analyst → (tools?) ─no→ generate → END
                        │yes
                        ▼
                      tools → grade ─sufficient→ generate → END
                                   └─thin──────→ rewrite → analyst

The loop is the reason this is a graph and not a single prompt. A first-pass web
search on an early-stage startup often returns very little, and asking the model
to write an investment thesis on thin evidence is how reports get invented. The
grader forces a second, narrower search instead — bounded to
``settings.max_query_rewrites`` so a genuinely unsearchable company still gets a
report, written from what is actually known.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from finagent import store
from finagent.agents import prompts
from finagent.agents.tools import EVALUATION_TOOLS
from finagent.services import mca, runtime, vectorstore
from finagent.settings import settings

logger = logging.getLogger(__name__)

MAX_DOC_CONTEXT_CHARS = 3000
MAX_CONTEXT_MESSAGES = 8
MIN_CONTEXT_CHARS = 50


class AnalysisState(TypedDict):
    """State carried between nodes."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    startup_id: str
    collection_name: str
    rewrite_count: int


# ─── Context assembly ─────────────────────────────────────────────────────────

def _document_context(query: str, collection_name: str, startup: dict[str, Any]) -> str:
    """Best available document context: vector hits, else raw extracted text."""
    context = vectorstore.retrieve(query, collection_name)
    if context:
        return context

    fallback = startup.get("extracted_text", "")
    if fallback:
        logger.info("Using in-memory extracted text for %s", startup.get("startup_id"))
        return fallback[:MAX_DOC_CONTEXT_CHARS]
    return "No documents have been uploaded for this startup."


def _last_message_text(messages: Sequence[BaseMessage]) -> str:
    if not messages:
        return ""
    content = messages[-1].content
    return content if isinstance(content, str) else str(content)


# ─── Nodes ────────────────────────────────────────────────────────────────────

def analyst_agent(state: AnalysisState) -> dict:
    """Assemble context and let the model decide whether to search."""
    logger.info("--- ANALYST AGENT ---")
    llm = runtime.get_llm()
    if llm is None:
        raise RuntimeError("LLM is not initialised")

    startup = store.get_startup(state["startup_id"]) or {}
    query = _last_message_text(state["messages"])[:500]

    system_prompt = prompts.ANALYST_SYSTEM.format(
        name=startup.get("name", "N/A"),
        domain=startup.get("domain", "N/A"),
        description=startup.get("description", "N/A"),
        team=startup.get("team", "N/A"),
        extras=startup.get("extras") or "N/A",
        verification=mca.summary_line(startup),
        documents=_document_context(query, state["collection_name"], startup),
    )

    try:
        response = llm.bind_tools(EVALUATION_TOOLS).invoke(
            [HumanMessage(content=system_prompt)] + list(state["messages"])
        )
        return {"messages": [response]}
    except Exception as exc:
        # Tool binding can fail on provider hiccups. Rather than abort the run,
        # emit a plain message so the graph routes straight to generation.
        logger.warning("Analyst tool binding failed: %s", exc)
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Tool invocation encountered a connectivity error. "
                        "Proceeding directly to generate the analysis report "
                        "using the startup profile and pre-trained knowledge."
                    )
                )
            ]
        }


def safe_tool_node(state: AnalysisState) -> dict:
    """Run the tools, converting failures into readable tool messages.

    A raised exception here would kill the whole evaluation. Instead each failed
    call becomes a ToolMessage that tells the model what went wrong, so it can
    continue with what it already has.
    """
    try:
        return ToolNode(EVALUATION_TOOLS).invoke(state)
    except Exception as exc:
        logger.warning("Tool execution failed (continuing): %s", exc)

    last_ai = next(
        (m for m in reversed(state.get("messages", [])) if isinstance(m, AIMessage)), None
    )
    calls = getattr(last_ai, "tool_calls", None) or []

    if calls:
        synthetic = [
            ToolMessage(
                content=(
                    f"[Tool failed due to a connectivity error] "
                    f"Use pre-trained knowledge to supplement the analysis. "
                    f"Query was: {call.get('args', {})}"
                ),
                tool_call_id=call.get("id", "fallback"),
                name=call.get("name", "unknown_tool"),
            )
            for call in calls
        ]
    else:
        synthetic = [
            ToolMessage(
                content="[All tool calls failed] Proceeding with pre-trained knowledge only.",
                tool_call_id="fallback",
                name="fallback",
            )
        ]
    return {"messages": synthetic}


def grade_relevance(state: AnalysisState) -> Literal["generate", "rewrite"]:
    """Decide whether the retrieved evidence supports a report."""
    logger.info("--- GRADE RELEVANCE ---")

    if state.get("rewrite_count", 0) >= settings.max_query_rewrites:
        logger.info("Rewrite budget exhausted — generating with what we have")
        return "generate"

    llm = runtime.get_llm()
    if llm is None:
        return "generate"

    content = _last_message_text(state["messages"])
    try:
        verdict = llm.invoke(
            [HumanMessage(content=prompts.RELEVANCE_GRADER.format(content=content[:800]))]
        )
        answer = str(verdict.content).strip().lower()
    except Exception as exc:
        # A grader failure should not cost the user their report.
        logger.warning("Relevance grading failed (%s) — generating", exc)
        return "generate"

    decision = "generate" if "yes" in answer else "rewrite"
    logger.info("Relevance verdict: %s", decision)
    return decision


def rewrite_query(state: AnalysisState) -> dict:
    """Produce a narrower query and send the analyst round again."""
    logger.info("--- REWRITE QUERY (attempt %d) ---", state.get("rewrite_count", 0) + 1)
    llm = runtime.get_llm()
    original = state["messages"][0].content if state["messages"] else ""

    try:
        response = llm.invoke(
            [HumanMessage(content=prompts.QUERY_REWRITER.format(query=original))]
        )
        rewritten = response.content
    except Exception as exc:
        logger.warning("Query rewrite failed (%s) — reusing the original", exc)
        rewritten = original

    return {
        "messages": [HumanMessage(content=rewritten)],
        "rewrite_count": state.get("rewrite_count", 0) + 1,
    }


def generate_analysis(state: AnalysisState) -> dict:
    """Write the final Markdown report from everything gathered."""
    logger.info("--- GENERATE ANALYSIS ---")
    llm = runtime.get_llm()
    startup = store.get_startup(state["startup_id"]) or {}
    messages = state["messages"]

    # Prefer tool output; fall back to the analyst's own reasoning when every
    # search failed, so the report still reflects the run.
    gathered: list[str] = [
        str(m.content).strip()
        for m in messages
        if isinstance(m, ToolMessage) and len(str(m.content).strip()) > MIN_CONTEXT_CHARS
    ]
    if not gathered:
        gathered = [
            str(m.content).strip()
            for m in messages
            if isinstance(m, AIMessage) and len(str(m.content).strip()) > MIN_CONTEXT_CHARS
        ]

    context = "\n\n---\n\n".join(gathered[-MAX_CONTEXT_MESSAGES:])

    prompt = prompts.REPORT_WRITER.format(
        name=startup.get("name", "N/A"),
        domain=startup.get("domain", "N/A"),
        description=startup.get("description", "N/A"),
        team=startup.get("team", "N/A"),
        extras=startup.get("extras") or "N/A",
        verification=mca.summary_line(startup),
        context=context or "No external research context was retrieved.",
    )

    try:
        return {"messages": [llm.invoke([HumanMessage(content=prompt)])]}
    except Exception as exc:
        logger.error("Report generation failed: %s", exc)
        return {
            "messages": [
                AIMessage(content="Analysis generation encountered an error. Please retry.")
            ]
        }


# ─── Graph ────────────────────────────────────────────────────────────────────

def build_graph():
    """Compile the evaluation workflow."""
    workflow = StateGraph(AnalysisState)

    workflow.add_node("analyst", analyst_agent)
    workflow.add_node("tools", safe_tool_node)
    workflow.add_node("rewrite", rewrite_query)
    workflow.add_node("generate", generate_analysis)

    workflow.add_edge(START, "analyst")
    workflow.add_conditional_edges(
        "analyst", tools_condition, {"tools": "tools", END: "generate"}
    )
    workflow.add_conditional_edges(
        "tools", grade_relevance, {"generate": "generate", "rewrite": "rewrite"}
    )
    workflow.add_edge("rewrite", "analyst")
    workflow.add_edge("generate", END)

    return workflow.compile()


def initial_state(startup: dict[str, Any]) -> AnalysisState:
    """Seed state for a full evaluation run."""
    query = (
        f"Perform a comprehensive evaluation of the startup '{startup['name']}' "
        f"operating in the '{startup['domain']}' industry. "
        f"Product: {startup['description']}. Team: {startup['team']}. "
        f"Additional context: {startup.get('extras') or 'None'}. "
        "Analyse uploaded documents, research current market trends, competition, "
        "TAM/SAM/SOM, the regulatory environment, and investment potential."
    )
    return {
        "messages": [HumanMessage(content=query)],
        "startup_id": startup["startup_id"],
        "collection_name": store.collection_name_for(startup["startup_id"]),
        "rewrite_count": 0,
    }


def run(startup: dict[str, Any]) -> str:
    """Execute the workflow synchronously and return the Markdown report."""
    graph = build_graph()
    result = graph.invoke(
        initial_state(startup), {"recursion_limit": settings.recursion_limit}
    )
    final = result["messages"][-1]
    return final.content if isinstance(final.content, str) else str(final.content)
