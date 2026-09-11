"""Startup record construction and normalisation.

Keeps the shape of a stored startup in one place so the API routes stay thin
and the legacy-frontend aliases are handled exactly once.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from finagent.schemas import StartupCreate
from finagent.services import mca

logger = logging.getLogger(__name__)

PLACEHOLDER = "N/A"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _extras_from_legacy(body: StartupCreate) -> str:
    """Fold the old frontend's separate fields into the free-text extras block."""
    parts = []
    if body.stage:
        parts.append(f"Stage: {body.stage}")
    if body.teamSize is not None:
        parts.append(f"Team Size: {body.teamSize}")
    if body.fundingRequired:
        parts.append(f"Funding Required: {body.fundingRequired}")
    return ", ".join(parts)


def build_record(body: StartupCreate) -> dict[str, Any]:
    """Create a startup record from a registration request."""
    startup_id = body.startupId or str(uuid.uuid4())
    now = utc_now()

    record: dict[str, Any] = {
        "startup_id": startup_id,
        # Mirrored keys kept for frontend clients that read `id` or `startupId`.
        "id": startup_id,
        "startupId": startup_id,
        "name": body.name,
        "domain": body.domain or PLACEHOLDER,
        "description": body.description or body.idea or PLACEHOLDER,
        "team": body.team or PLACEHOLDER,
        "extras": body.extras or _extras_from_legacy(body) or None,
        "created_at": now,
        "updated_at": now,
        "document_collections": [],
        "extracted_text": "",
        "verification": mca.empty_verification(),
    }
    return record


def apply_update(record: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    record.update(updates)
    record["updated_at"] = utc_now()
    return record


def parse_analysis_sections(analysis_text: str) -> dict[str, Any]:
    """Split the Markdown report into the sections the dashboard renders."""
    import re

    def section(title: str) -> str:
        match = re.search(
            rf"(?i)##\s*\d*\.?\s*\**{re.escape(title)}\**.*?\n(.*?)(?=\n##|\Z)",
            analysis_text,
            re.DOTALL,
        )
        return match.group(1).strip() if match else f"See the full report for {title}."

    return {
        "executiveSummary": section("Executive Summary"),
        "marketAnalysis": section("Market Opportunity"),
        "teamAssessment": section("Team Assessment"),
        "riskFactors": section("Risks & Challenges"),
        "recommendation": section("Recommendation"),
        "score": 8.5,
    }


def maybe_autoverify_sandbox(record: dict[str, Any]) -> bool:
    """Pre-verify the sandbox demo company at registration time.

    Only fires when the registry provider is the sandbox and the submitted name
    matches the sandbox company exactly. It exists so the "verified" path of the
    report can be demonstrated without a paid registry subscription; with
    ``MCA_API_KEY`` set this is a no-op and verification must be requested
    explicitly via ``POST /startups/{id}/verify/mca``.
    """
    from finagent.settings import settings

    if settings.mca_live:
        return False

    result = mca.sandbox_response("AUTO")
    sandbox_name = (result.get("company_name") or "").strip().lower()
    if not sandbox_name or sandbox_name != record["name"].strip().lower():
        return False
    if not result.get("valid"):
        return False

    mca.apply_result(record, "AUTO_VERIFIED", result)
    logger.info("Auto-verified '%s' against the sandbox registry", record["name"])
    return True
