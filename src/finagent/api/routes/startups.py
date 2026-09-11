"""Startup registration and profile management."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends

from finagent import store
from finagent.api.deps import require_startup
from finagent.schemas import StartupCreate, StartupResponse, StartupUpdate
from finagent.services import startups as startup_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Startups"])


@router.post("/startups", status_code=201, response_model=StartupResponse,
             summary="Register a new startup")
async def create_startup(body: StartupCreate) -> StartupResponse:
    record = startup_service.build_record(body)
    startup_service.maybe_autoverify_sandbox(record)
    store.save_startup(record)
    logger.info("Startup registered: %s — %s", record["startup_id"], record["name"])
    return StartupResponse(**record)


@router.put("/startups/{startup_id}", response_model=StartupResponse,
            summary="Update an existing startup profile")
async def update_startup(
    body: StartupUpdate,
    record: dict[str, Any] = Depends(require_startup),
) -> StartupResponse:
    updated = startup_service.apply_update(record, body.model_dump(exclude_none=True))
    store.save_startup(updated)
    logger.info("Startup updated: %s", updated["startup_id"])
    return StartupResponse(**updated)


@router.get("/startups", response_model=list[StartupResponse],
            summary="List all registered startups")
async def list_startups() -> list[StartupResponse]:
    return [StartupResponse(**record) for record in store.list_startups()]


@router.get("/startups/{startup_id}", response_model=StartupResponse,
            summary="Get a startup by ID")
async def get_startup(record: dict[str, Any] = Depends(require_startup)) -> StartupResponse:
    return StartupResponse(**record)


# ── Compatibility alias for the Express-era frontend ──────────────────────────

@router.post("/api/startups/register", status_code=201, response_model=StartupResponse,
             include_in_schema=False)
async def register_startup_alias(body: StartupCreate) -> StartupResponse:
    return await create_startup(body)
