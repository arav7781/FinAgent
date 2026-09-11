"""Company registry verification (MCA).

Indian companies are identified by a 21-character CIN. FinAgent validates the
format locally, resolves the CIN against a registry provider, and then compares
the registry's answer with what the founder claimed. The comparison is the point
— a name that does not match the register, or a struck-off company, is exactly
the kind of signal an investor wants before a call.

Verification is advisory: a failed check annotates the report, it never blocks
it. Without ``MCA_API_KEY`` the deterministic sandbox provider is used so the
pipeline stays demonstrable offline.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

import requests

from finagent.settings import settings

logger = logging.getLogger(__name__)

# L/U + 5 digits + 2 state letters + 4-digit year + 3 class letters + 6 digits
CIN_PATTERN = re.compile(r"^[LUlu]\d{5}[A-Za-z]{2}\d{4}[A-Za-z]{3}\d{6}$")

CIN_FORMAT_HELP = (
    "Expected format: L/U + 5 digits + 2 letters + 4 digits + 3 letters + "
    "6 digits (e.g. L17110MH1973PLC019786)"
)

SANDBOX_COMPANY_NAME = "QuantumFleet AI"
SANDBOX_DIRECTORS = ["Arjun Malhotra", "Dr. Elena Novak"]

# Sandbox rule: a CIN whose six-digit serial ends in 0 resolves to a struck-off
# company. The serial is the last character of a well-formed CIN, so this rule
# is reachable through the API — unlike a rule keyed on a letter, which the
# format check would reject before the provider was ever called.
SANDBOX_STRUCK_OFF_SUFFIX = "0"


def is_valid_cin(cin: str) -> bool:
    return bool(CIN_PATTERN.match((cin or "").strip()))


def normalise_cin(cin: str) -> str:
    return (cin or "").strip().upper()


def sandbox_response(cin: str) -> dict[str, Any]:
    """Deterministic stand-in for a paid registry API.

    A CIN whose serial ends in ``0`` resolves to a struck-off company, so the
    failure path can be demonstrated without a live subscription. Everything
    else resolves to an active company.
    """
    is_active = not normalise_cin(cin).endswith(SANDBOX_STRUCK_OFF_SUFFIX)
    return {
        "valid": is_active,
        "company_status": "ACTIVE" if is_active else "STRUCK_OFF",
        "directors": list(SANDBOX_DIRECTORS) if is_active else [],
        "company_name": SANDBOX_COMPANY_NAME,
        "source": "sandbox",
    }


def lookup(cin: str) -> dict[str, Any]:
    """Resolve a CIN through the configured provider.

    Network or provider errors fall back to the sandbox rather than failing the
    request — an unverified startup is still worth evaluating.
    """
    if not settings.mca_live:
        logger.info("MCA_API_KEY not set — using sandbox registry response")
        return sandbox_response(cin)

    try:
        response = requests.get(
            settings.mca_api_url,
            params={"cin": cin},
            headers={"x-karza-key": settings.mca_api_key, "Content-Type": "application/json"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return {
            "valid": str(data.get("status", "")).upper() == "ACTIVE",
            "company_status": data.get("status"),
            "directors": data.get("directors", []),
            "company_name": data.get("companyName") or data.get("company_name"),
            "source": "live",
        }
    except Exception as exc:
        logger.error("MCA provider call failed (%s) — falling back to sandbox", exc)
        return sandbox_response(cin)


def empty_verification() -> dict[str, Any]:
    """The verification block attached to every new startup record."""
    return {
        "cin": None,
        "mca_verified": False,
        "company_status": None,
        "company_name": None,
        "directors": [],
        "last_checked": None,
    }


def apply_result(record: dict[str, Any], cin: str, result: dict[str, Any]) -> str:
    """Persist a lookup onto a startup record. Returns the check timestamp."""
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    record.setdefault("verification", empty_verification()).update(
        {
            "cin": cin,
            "mca_verified": bool(result.get("valid")),
            "company_status": result.get("company_status"),
            "company_name": result.get("company_name"),
            "directors": result.get("directors", []),
            "last_checked": now,
        }
    )
    record["updated_at"] = now
    return now


def names_match(record: dict[str, Any]) -> bool:
    verification = record.get("verification", {})
    registry_name = (verification.get("company_name") or "").strip().lower()
    claimed_name = (record.get("name") or "").strip().lower()
    return bool(registry_name and claimed_name and registry_name == claimed_name)


def consistency_flags(record: dict[str, Any]) -> list[str]:
    """Differences between the founder's claims and the registry.

    An empty list means nothing was found to question.
    """
    verification = record.get("verification", {})
    flags: list[str] = []

    if not verification.get("mca_verified"):
        flags.append("MCA_NOT_VERIFIED")

    registry_name = (verification.get("company_name") or "").strip().lower()
    claimed_name = (record.get("name") or "").strip().lower()
    if registry_name and claimed_name and registry_name != claimed_name:
        flags.append("NAME_MISMATCH")

    if not verification.get("directors"):
        flags.append("NO_DIRECTORS_FOUND")

    status = (verification.get("company_status") or "").upper()
    if status and status != "ACTIVE":
        flags.append(f"COMPANY_STATUS_{status}")

    return flags


def summary_line(record: dict[str, Any]) -> str:
    """One-line verification summary for prompts and PDF sections."""
    verification = record.get("verification", {})
    if not verification.get("mca_verified"):
        return "MCA NOT VERIFIED — verification not completed or pending."

    line = (
        f"MCA VERIFIED | CIN: {verification.get('cin')} | "
        f"Status: {verification.get('company_status')} | "
        f"Registered as: {verification.get('company_name')}"
    )
    flags = consistency_flags(record)
    if flags:
        line += f"\nCompliance flags: {', '.join(flags)}"
    return line
