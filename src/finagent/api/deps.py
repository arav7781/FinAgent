"""Shared route dependencies and error helpers."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Path

from finagent import store


def require_startup(startup_id: str = Path(..., description="The unique startup ID")) -> dict[str, Any]:
    """Load a startup or raise 404."""
    record = store.get_startup(startup_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Startup '{startup_id}' not found")
    return record


def require_llm() -> Any:
    from finagent.services import runtime

    llm = runtime.get_llm()
    if llm is None:
        raise HTTPException(status_code=503, detail="LLM is not available")
    return llm
