"""In-memory repositories.

FinAgent keeps startup records and analysis results in process memory. This is
deliberate for an evaluation build: it removes database setup from the critical
path. The accessors below are the single seam to swap in a real database — the
API and agent layers never touch the dictionaries directly.
"""

from __future__ import annotations

from typing import Any

# { startup_id: startup record }
_startups: dict[str, dict[str, Any]] = {}

# { startup_id: { "status": ..., "analysis": ... } }
_analyses: dict[str, dict[str, Any]] = {}


# ─── Startups ─────────────────────────────────────────────────────────────────

def save_startup(record: dict[str, Any]) -> dict[str, Any]:
    _startups[record["startup_id"]] = record
    return record


def get_startup(startup_id: str) -> dict[str, Any] | None:
    return _startups.get(startup_id)


def list_startups() -> list[dict[str, Any]]:
    return list(_startups.values())


def find_startup_by_name(name: str) -> dict[str, Any] | None:
    """Return the most recently registered startup with this name.

    Names are not unique, so the newest record wins — that is the one a user who
    just registered a startup expects to talk to.
    """
    target = (name or "").strip().lower()
    match: dict[str, Any] | None = None
    for record in _startups.values():
        if record.get("name", "").strip().lower() == target:
            if match is None or record["created_at"] > match["created_at"]:
                match = record
    return match


def collection_name_for(startup_id: str) -> str:
    """Qdrant collection holding one startup's document chunks."""
    return f"startup_{startup_id.replace('-', '')}"


# ─── Analysis results ─────────────────────────────────────────────────────────

def set_analysis(startup_id: str, payload: dict[str, Any]) -> None:
    _analyses[startup_id] = payload


def get_analysis(startup_id: str) -> dict[str, Any] | None:
    return _analyses.get(startup_id)


def reset() -> None:
    """Clear all state. Used by the test-suite between cases."""
    _startups.clear()
    _analyses.clear()
