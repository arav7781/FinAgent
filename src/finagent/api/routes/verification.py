"""MCA registry verification endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from finagent import store
from finagent.api.deps import require_startup
from finagent.schemas import (
    MCAStatusResponse,
    MCAVerificationRequest,
    MCAVerificationResponse,
)
from finagent.services import mca

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Verification"])


@router.post("/startups/{startup_id}/verify/mca", response_model=MCAVerificationResponse,
             summary="Verify a startup against the MCA registry by CIN")
async def verify_mca(
    body: MCAVerificationRequest,
    record: dict[str, Any] = Depends(require_startup),
) -> MCAVerificationResponse:
    """Resolve the CIN and store the outcome on the startup record.

    A malformed CIN is rejected locally (422) before any provider call. A
    well-formed CIN that resolves to an inactive company returns 400 with the
    registry status — the result is still persisted so the report can cite it.
    """
    cin = mca.normalise_cin(body.cin)
    if not cin:
        raise HTTPException(status_code=400, detail="CIN cannot be empty")
    if not mca.is_valid_cin(cin):
        raise HTTPException(status_code=422, detail=f"Invalid CIN format. {mca.CIN_FORMAT_HELP}")

    logger.info("MCA verification requested for %s with CIN %s", record["startup_id"], cin)
    result = mca.lookup(cin)
    checked_at = mca.apply_result(record, cin, result)
    store.save_startup(record)

    if not result.get("valid"):
        status = result.get("company_status", "UNKNOWN")
        logger.warning("MCA verification failed for %s: %s", record["startup_id"], status)
        raise HTTPException(
            status_code=400,
            detail=(
                f"CIN {cin} is not active in the MCA registry. Status: {status}. "
                "Verify the CIN and try again, or proceed without verification."
            ),
        )

    flags = mca.consistency_flags(record)
    logger.info("MCA verified: %s | flags: %s", record["startup_id"], flags)

    return MCAVerificationResponse(
        startup_id=record["startup_id"],
        cin=cin,
        mca_verified=True,
        company_status=result.get("company_status"),
        company_name=result.get("company_name"),
        directors=result.get("directors", []),
        name_match=mca.names_match(record),
        flags=flags,
        last_checked=checked_at,
        message="Verification successful." if not flags
        else f"Verified with warnings: {', '.join(flags)}",
    )


@router.get("/startups/{startup_id}/verify/mca", response_model=MCAStatusResponse,
            summary="Get the stored MCA verification status")
async def mca_status(record: dict[str, Any] = Depends(require_startup)) -> MCAStatusResponse:
    """Read back the last verification without re-calling the provider."""
    verification = record.get("verification", {})
    return MCAStatusResponse(
        startup_id=record["startup_id"],
        cin=verification.get("cin"),
        mca_verified=bool(verification.get("mca_verified")),
        company_status=verification.get("company_status"),
        company_name=verification.get("company_name"),
        directors=verification.get("directors", []),
        flags=mca.consistency_flags(record),
        last_checked=verification.get("last_checked"),
    )
