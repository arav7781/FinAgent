"""Report generation — synchronous PDF and background JSON analysis."""

from __future__ import annotations

import asyncio
import io
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse

from finagent import store
from finagent.agents import evaluation_graph
from finagent.api.deps import require_startup
from finagent.services import mca, report
from finagent.services import startups as startup_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Reports"])


@router.post("/reports/{startup_id}", summary="Run the evaluation pipeline and return a PDF")
async def generate_report(record: dict[str, Any] = Depends(require_startup)) -> StreamingResponse:
    """Run the full pipeline and stream the investor PDF back.

    Registry flags are logged as warnings but never block the report —
    an unverified startup is still worth an assessment, provided the report
    says so, which it does.
    """
    flags = mca.consistency_flags(record)
    if flags:
        logger.info("Report for %s carries flags: %s", record["startup_id"], flags)

    try:
        analysis = await asyncio.to_thread(evaluation_graph.run, record)
    except Exception as exc:
        logger.error("Evaluation pipeline failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"AI analysis pipeline failed: {exc}") from exc

    try:
        pdf_bytes = await asyncio.to_thread(report.build_pdf, record, analysis)
    except Exception as exc:
        logger.error("PDF rendering failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}") from exc

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{report.filename_for(record)}"'},
    )


@router.post("/api/startups/{startup_id}/analyze", summary="Start a background analysis")
async def trigger_analysis(
    background_tasks: BackgroundTasks,
    record: dict[str, Any] = Depends(require_startup),
) -> dict[str, str]:
    """Kick off the pipeline and return immediately.

    A full run takes tens of seconds, which is longer than a browser request
    should hold open, so the result is polled from the status endpoint.
    """
    startup_id = record["startup_id"]
    store.set_analysis(startup_id, {"status": "processing", "analysis": None})
    background_tasks.add_task(run_analysis_task, startup_id)
    return {"status": "analysis_started", "id": startup_id}


@router.get("/api/startups/{startup_id}/report/status", summary="Poll background analysis status")
async def analysis_status(startup_id: str) -> dict[str, Any]:
    return store.get_analysis(startup_id) or {"status": "not_started"}


async def run_analysis_task(startup_id: str) -> None:
    """Background worker: run the graph and store parsed sections."""
    try:
        record = store.get_startup(startup_id)
        if record is None:
            raise ValueError(f"Startup '{startup_id}' disappeared before analysis")

        analysis_text = await asyncio.to_thread(evaluation_graph.run, record)
        store.set_analysis(startup_id, {
            "status": "complete",
            "analysis": startup_service.parse_analysis_sections(analysis_text),
        })
        logger.info("Background analysis complete for %s", startup_id)
    except Exception as exc:
        logger.error("Background analysis failed for %s: %s", startup_id, exc)
        store.set_analysis(startup_id, {"status": "failed", "error": str(exc)})
