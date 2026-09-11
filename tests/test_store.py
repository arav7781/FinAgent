"""In-memory repository behaviour."""

from finagent import store


def test_save_and_get_roundtrip(startup_record):
    store.save_startup(startup_record)
    assert store.get_startup(startup_record["startup_id"])["name"] == "QuantumFleet AI"


def test_get_missing_returns_none():
    assert store.get_startup("does-not-exist") is None


def test_list_returns_every_record(startup_record):
    store.save_startup(startup_record)
    store.save_startup({**startup_record, "startup_id": "second", "name": "Other"})
    assert len(store.list_startups()) == 2


def test_find_by_name_is_case_insensitive(startup_record):
    store.save_startup(startup_record)
    assert store.find_startup_by_name("quantumfleet ai") is not None
    assert store.find_startup_by_name("  QUANTUMFLEET AI  ") is not None


def test_find_by_name_returns_the_newest_duplicate(startup_record):
    """Duplicate names resolve to the most recently registered startup."""
    store.save_startup({**startup_record, "startup_id": "old", "created_at": "2026-01-01T00:00:00Z"})
    store.save_startup({**startup_record, "startup_id": "new", "created_at": "2026-06-01T00:00:00Z"})
    assert store.find_startup_by_name("QuantumFleet AI")["startup_id"] == "new"


def test_find_by_name_missing_returns_none():
    assert store.find_startup_by_name("Nothing Here") is None


def test_collection_name_strips_hyphens():
    assert store.collection_name_for("aaaa-bbbb-cccc") == "startup_aaaabbbbcccc"


def test_analysis_roundtrip():
    store.set_analysis("abc", {"status": "processing", "analysis": None})
    assert store.get_analysis("abc")["status"] == "processing"
    assert store.get_analysis("missing") is None


def test_reset_clears_everything(startup_record):
    store.save_startup(startup_record)
    store.set_analysis("abc", {"status": "complete"})
    store.reset()
    assert store.list_startups() == []
    assert store.get_analysis("abc") is None
