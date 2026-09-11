"""CIN validation, registry lookup, and consistency flagging."""

import pytest

from finagent.services import mca


@pytest.mark.parametrize("cin", [
    "L17110MH1973PLC019786",
    "U72900MH2021PTC123456",
    "u72900mh2021ptc123456",  # lowercase is accepted, normalised on write
])
def test_accepts_wellformed_cin(cin):
    assert mca.is_valid_cin(cin)


@pytest.mark.parametrize("cin", [
    "",
    "NOTACIN",
    "L17110MH1973PLC01978",     # one digit short
    "X17110MH1973PLC019786",    # must start with L or U
    "L1711MH1973PLC019786",     # four leading digits
    "L17110MH19731PLC019786",   # five-digit year
])
def test_rejects_malformed_cin(cin):
    assert not mca.is_valid_cin(cin)


def test_normalise_uppercases_and_strips():
    assert mca.normalise_cin("  u72900mh2021ptc123456 ") == "U72900MH2021PTC123456"


def test_sandbox_marks_active_company():
    result = mca.sandbox_response("U72900MH2021PTC123456")
    assert result["valid"] is True
    assert result["company_status"] == "ACTIVE"
    assert result["directors"]


def test_sandbox_marks_struck_off_company():
    """A serial ending in 0 models the struck-off path, and is a valid CIN."""
    assert mca.is_valid_cin("U72900MH2021PTC123450")
    result = mca.sandbox_response("U72900MH2021PTC123450")
    assert result["valid"] is False
    assert result["company_status"] == "STRUCK_OFF"
    assert result["directors"] == []


def test_lookup_uses_sandbox_without_api_key():
    assert mca.lookup("U72900MH2021PTC123456")["source"] == "sandbox"


def test_unverified_startup_is_flagged(startup_record):
    flags = mca.consistency_flags(startup_record)
    assert "MCA_NOT_VERIFIED" in flags
    assert "NO_DIRECTORS_FOUND" in flags


def test_verified_matching_startup_has_no_flags(verified_record):
    # The fixture's name matches the sandbox company exactly.
    assert mca.consistency_flags(verified_record) == []
    assert mca.names_match(verified_record)


def test_name_mismatch_is_flagged(verified_record):
    verified_record["name"] = "Some Other Company"
    flags = mca.consistency_flags(verified_record)
    assert "NAME_MISMATCH" in flags
    assert not mca.names_match(verified_record)


def test_inactive_status_is_flagged(startup_record):
    mca.apply_result(
        startup_record,
        "U72900MH2021PTC123450",
        mca.sandbox_response("U72900MH2021PTC123450"),
    )
    assert "COMPANY_STATUS_STRUCK_OFF" in mca.consistency_flags(startup_record)


def test_apply_result_persists_and_timestamps(startup_record):
    checked_at = mca.apply_result(
        startup_record, "U72900MH2021PTC123456",
        mca.sandbox_response("U72900MH2021PTC123456"),
    )
    verification = startup_record["verification"]
    assert verification["mca_verified"] is True
    assert verification["cin"] == "U72900MH2021PTC123456"
    assert verification["last_checked"] == checked_at
    assert startup_record["updated_at"] == checked_at


def test_summary_line_reflects_state(startup_record, verified_record):
    assert "NOT VERIFIED" in mca.summary_line(startup_record)
    assert "MCA VERIFIED" in mca.summary_line(verified_record)
