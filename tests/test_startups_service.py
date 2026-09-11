"""Record construction, legacy-field normalisation and section parsing."""

from finagent.schemas import StartupCreate
from finagent.services import startups as startup_service


def test_builds_record_with_generated_id():
    record = startup_service.build_record(StartupCreate(name="Acme AI", domain="Fintech"))
    assert record["startup_id"]
    assert record["id"] == record["startup_id"] == record["startupId"]
    assert record["name"] == "Acme AI"
    assert record["verification"]["mca_verified"] is False


def test_honours_client_supplied_id():
    record = startup_service.build_record(StartupCreate(name="Acme", startupId="fixed-id"))
    assert record["startup_id"] == "fixed-id"


def test_legacy_idea_field_becomes_description():
    record = startup_service.build_record(StartupCreate(name="Acme", idea="An AI for ledgers"))
    assert record["description"] == "An AI for ledgers"


def test_legacy_fields_fold_into_extras():
    record = startup_service.build_record(
        StartupCreate(name="Acme", stage="Seed", teamSize=6, fundingRequired="$500k")
    )
    assert "Stage: Seed" in record["extras"]
    assert "Team Size: 6" in record["extras"]
    assert "Funding Required: $500k" in record["extras"]


def test_explicit_extras_wins_over_legacy_fields():
    record = startup_service.build_record(
        StartupCreate(name="Acme", extras="Handwritten note", stage="Seed")
    )
    assert record["extras"] == "Handwritten note"


def test_missing_optional_fields_become_placeholders():
    record = startup_service.build_record(StartupCreate(name="Acme"))
    assert record["domain"] == startup_service.PLACEHOLDER
    assert record["description"] == startup_service.PLACEHOLDER
    assert record["extras"] is None


def test_update_refreshes_timestamp(startup_record):
    before = startup_record["updated_at"]
    updated = startup_service.apply_update(startup_record, {"domain": "Healthcare AI"})
    assert updated["domain"] == "Healthcare AI"
    assert updated["updated_at"] != before


def test_sandbox_autoverify_matches_only_the_demo_company():
    matching = startup_service.build_record(StartupCreate(name="QuantumFleet AI"))
    other = startup_service.build_record(StartupCreate(name="Some Other Startup"))

    assert startup_service.maybe_autoverify_sandbox(matching) is True
    assert matching["verification"]["mca_verified"] is True

    assert startup_service.maybe_autoverify_sandbox(other) is False
    assert other["verification"]["mca_verified"] is False


REPORT = """## 1. Executive Summary
A seed-stage logistics AI company with early traction.

## 2. Market Opportunity
TAM is estimated at $100B growing 24% year on year.

## 3. Team Assessment
Two technical founders, no commercial lead yet.

## 4. Risks & Challenges
Concentration risk: one customer is 60% of revenue.

## 5. Recommendation
Buy, subject to a commercial hire.
"""


def test_parses_each_report_section():
    sections = startup_service.parse_analysis_sections(REPORT)
    assert "early traction" in sections["executiveSummary"]
    assert "$100B" in sections["marketAnalysis"]
    assert "commercial lead" in sections["teamAssessment"]
    assert "Concentration risk" in sections["riskFactors"]
    assert "Buy" in sections["recommendation"]


def test_missing_section_degrades_to_a_pointer():
    sections = startup_service.parse_analysis_sections("## Executive Summary\nOnly this.")
    assert "See the full report" in sections["teamAssessment"]
