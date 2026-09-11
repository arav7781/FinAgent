"""Agent routing and graph decision logic (no live model calls)."""

import pytest

from finagent.agents import evaluation_graph, finscope_graph
from finagent.settings import settings

# ─── FinScope routing ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("intent,expected", [
    ("education", "financial_educator"),
    ("document", "document_analyzer"),
    ("market", "market_researcher"),
    ("strategy", "portfolio_coach"),
    ("news", "news_reporter"),
])
def test_every_intent_has_a_subagent(intent, expected):
    assert finscope_graph.route_to_subagent({"intent": intent}) == expected


def test_unknown_intent_falls_back_to_the_educator():
    assert finscope_graph.route_to_subagent({"intent": "nonsense"}) == "financial_educator"
    assert finscope_graph.route_to_subagent({}) == "financial_educator"


def _state(text, document_text=""):
    from langchain_core.messages import HumanMessage

    return {
        "messages": [HumanMessage(content=text)],
        "intent": "",
        "document_text": document_text,
        "user_profile": "beginner",
    }


def test_video_request_short_circuits_to_education():
    """Keyword fast-paths must not need a model call."""
    assert classify("Show me a youtube video about ETFs") == "education"
    assert classify("any good video on compounding?") == "education"


def test_news_request_short_circuits_to_news():
    assert classify("latest news on Infosys") == "news"
    assert classify("what's happening with Tesla") == "news"
    assert classify("breaking headlines today") == "news"


def test_document_questions_route_to_document_when_one_is_loaded():
    assert classify("what does this document say?", document_text="Revenue...") == "document"


def test_document_keywords_without_a_document_do_not_route_to_document():
    """With no document loaded the classifier must not claim to read one."""
    assert classify("tell me about this company") != "document"


def classify(text, document_text=""):
    return finscope_graph.classify_intent(_state(text, document_text))["intent"]


def test_every_subagent_is_wired_into_the_graph():
    assert set(finscope_graph.SUBAGENTS) == set(finscope_graph.SUBAGENT_FOR_INTENT.values())
    assert set(finscope_graph.SUBAGENT_FOR_INTENT) == set(finscope_graph.INTENTS)


def test_session_documents_are_stored_and_cleared():
    finscope_graph.store_session_document("s1", "Pitch deck text")
    assert finscope_graph.get_session_document("s1") == "Pitch deck text"
    finscope_graph.clear_session("s1")
    assert finscope_graph.get_session_document("s1") == ""


def test_news_formatting_handles_no_articles():
    assert "No live news data" in finscope_graph._format_news([])


def test_news_formatting_includes_article_fields():
    block = finscope_graph._format_news([
        {"article_title": "Q3 beat", "source": "Reuters", "snippet": "Revenue rose."}
    ])
    assert "Q3 beat" in block and "Reuters" in block


# ─── Evaluation graph ─────────────────────────────────────────────────────────

def _analysis_state(rewrite_count=0, text="Some retrieved market context."):
    from langchain_core.messages import HumanMessage

    return {
        "messages": [HumanMessage(content=text)],
        "startup_id": "abc",
        "collection_name": "startup_abc",
        "rewrite_count": rewrite_count,
    }


def test_grader_sends_thin_results_back_for_a_rewrite(stub_llm):
    stub_llm.reply = "no"
    assert evaluation_graph.grade_relevance(_analysis_state()) == "rewrite"


def test_grader_accepts_sufficient_results(stub_llm):
    stub_llm.reply = "yes"
    assert evaluation_graph.grade_relevance(_analysis_state()) == "generate"


def test_rewrite_budget_is_enforced(stub_llm):
    """Past the budget the report is written regardless of the grader."""
    stub_llm.reply = "no"
    state = _analysis_state(rewrite_count=settings.max_query_rewrites)
    assert evaluation_graph.grade_relevance(state) == "generate"


def test_grader_failure_does_not_block_the_report(monkeypatch):
    class BrokenLLM:
        def invoke(self, *_args, **_kwargs):
            raise RuntimeError("provider down")

    from finagent.services import runtime

    monkeypatch.setattr(runtime, "get_llm", lambda: BrokenLLM())
    assert evaluation_graph.grade_relevance(_analysis_state()) == "generate"


def test_rewrite_increments_the_counter(stub_llm):
    stub_llm.reply = "A narrower query about logistics AI market size"
    result = evaluation_graph.rewrite_query(_analysis_state(rewrite_count=1))
    assert result["rewrite_count"] == 2
    assert result["messages"]


def test_initial_state_seeds_the_query(startup_record):
    state = evaluation_graph.initial_state(startup_record)
    query = state["messages"][0].content
    assert "QuantumFleet AI" in query
    assert "Logistics AI" in query
    assert state["rewrite_count"] == 0
    assert state["collection_name"].startswith("startup_")


def test_tool_failure_produces_a_readable_tool_message(monkeypatch):
    """A failing tool must not abort the run."""
    class Boom:
        def __init__(self, *_a, **_k):
            pass

        def invoke(self, *_a, **_k):
            raise RuntimeError("network unreachable")

    monkeypatch.setattr(evaluation_graph, "ToolNode", Boom)
    result = evaluation_graph.safe_tool_node(_analysis_state())
    assert result["messages"]
    assert "failed" in str(result["messages"][0].content).lower()
