"""FinScope advisory endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from finagent import realtime
from finagent.agents import finscope_graph, guardrails
from finagent.schemas import FinScopeChatRequest, FinScopeChatResponse
from finagent.services import documents, market_data

logger = logging.getLogger(__name__)

router = APIRouter(tags=["FinScope"])

MAX_HEADLINES = 20


@router.post("/finscope/chat", response_model=FinScopeChatResponse,
             summary="Send a message to the FinScope advisory router")
async def finscope_chat(body: FinScopeChatRequest) -> FinScopeChatResponse:
    """Guardrail the message, then route it to the right subagent."""
    offending = guardrails.matched_pattern(body.question)
    if offending:
        logger.warning("FinScope request blocked by guardrail: %r", offending)
        raise HTTPException(status_code=400, detail=guardrails.REFUSAL_MESSAGE)

    await realtime.broadcast("FinScope: processing chat request")
    try:
        result = await finscope_graph.run_chat(
            question=body.question,
            user_profile=body.user_profile,
            session_id=body.session_id,
        )
    except Exception as exc:
        logger.error("FinScope chat failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"FinScope chat failed: {exc}") from exc

    return FinScopeChatResponse(
        answer=result.get("answer", ""),
        agent_used=result.get("agent", "Financial Educator"),
        intent=result.get("intent", "education"),
    )


@router.post("/finscope/analyze-document", summary="Analyse a document into FinScope flashcards")
async def finscope_analyze_document(
    document: UploadFile = File(...),
    session_id: str = Form(""),
    user_profile: str = Form("beginner"),
) -> dict[str, Any]:
    """Extract a document and hand it to the Document Analyzer subagent.

    The text is cached against ``session_id`` so follow-up questions in the same
    chat resolve without a second upload.
    """
    await realtime.broadcast(f"FinScope: analyzing document {document.filename or 'upload'}")

    file_bytes = await document.read()
    suffix = documents.suffix_for(document.filename or "upload.pdf")
    try:
        chunks = await documents.extract_content(file_bytes, suffix=suffix)
    except documents.DocumentError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    document_text = "\n\n".join(chunk.page_content for chunk in chunks)
    if session_id:
        finscope_graph.store_session_document(session_id, document_text)

    try:
        result = await finscope_graph.run_chat(
            question="Analyze this document for an investor.",
            user_profile=user_profile,
            document_text=document_text,
            session_id=session_id,
        )
    except Exception as exc:
        logger.error("FinScope document analysis failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Document analysis failed: {exc}") from exc

    return {
        "analysis": result.get("answer", ""),
        "agent_used": result.get("agent", "Document Analyzer"),
        "intent": result.get("intent", "document"),
    }


@router.get("/api/finance-news/headlines", summary="Fetch live headlines for a symbol")
async def finance_headlines(symbol: str = "AAPL:NASDAQ", limit: int = 10) -> dict[str, Any]:
    """Raw headlines, for a UI ticker that does not need a model in the loop."""
    bounded = max(1, min(limit, MAX_HEADLINES))
    return {"headlines": market_data.fetch_news(symbol, bounded)}
