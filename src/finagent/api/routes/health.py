"""Liveness and dependency readiness."""

from __future__ import annotations

from fastapi import APIRouter

from finagent import __version__, store
from finagent.schemas import HealthResponse
from finagent.services import runtime
from finagent.settings import settings

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health() -> HealthResponse:
    """Report which optional dependencies actually came up.

    The service stays healthy with degraded dependencies — this endpoint is how
    an operator sees that retrieval or document conversion is running in
    fallback mode.
    """
    dependencies = runtime.status()
    return HealthResponse(
        status="healthy",
        service="FinAgent",
        version=__version__,
        startups_loaded=len(store.list_startups()),
        mca_api_configured=settings.mca_live,
        **dependencies,
    )
