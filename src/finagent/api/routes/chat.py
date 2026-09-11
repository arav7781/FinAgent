"""Investor Q&A against a single registered startup."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path
from langchain_core.messages import HumanMessage

from finagent import store
from finagent.agents import prompts
from finagent.api.deps import require_llm, require_startup
from finagent.schemas import ChatMessage, ChatResponse
from finagent.services import mca, vectorstore

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Investor Chat"])

MAX_FALLBACK_CHARS = 3000


async def _answer(record: dict[str, Any], question: str) -> ChatResponse:
    llm = require_llm()
    question = (question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    collection = store.collection_name_for(record["startup_id"])
    document_context = vectorstore.retrieve(question, collection)
    if not document_context:
        document_context = record.get("extracted_text", "")[:MAX_FALLBACK_CHARS]

    profile = (
        f"Startup: {record.get('name', 'N/A')}\n"
        f"Domain: {record.get('domain', 'N/A')}\n"
        f"Description: {record.get('description', 'N/A')}\n"
        f"Team: {record.get('team', 'N/A')}\n"
        f"Additional Info: {record.get('extras') or 'N/A'}\n"
        f"{mca.summary_line(record)}"
    )

    prompt = prompts.INVESTOR_CHAT.format(
        profile=profile,
        documents=document_context or "No documents available.",
        question=question,
    )

    try:
        response = await asyncio.to_thread(llm.invoke, [HumanMessage(content=prompt)])
    except Exception as exc:
        logger.error("Investor chat failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Chat failed: {exc}") from exc

    return ChatResponse(
        answer=str(response.content).strip(),
        startup_name=record.get("name", "Unknown"),
    )


@router.post("/chat/{startup_id}", response_model=ChatResponse,
             summary="Ask a question about a startup (by ID)")
async def chat_by_id(
    message: ChatMessage,
    record: dict[str, Any] = Depends(require_startup),
) -> ChatResponse:
    return await _answer(record, message.question)


@router.post("/chat/by-name/{startup_name}", response_model=ChatResponse,
             summary="Ask a question about a startup (by name)")
async def chat_by_name(
    message: ChatMessage,
    startup_name: str = Path(..., description="The startup name (case-insensitive)"),
) -> ChatResponse:
    record = store.find_startup_by_name(startup_name)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No startup named '{startup_name}' found. "
                "Register it first via POST /startups, then use its startup_id."
            ),
        )
    return await _answer(record, message.question)
