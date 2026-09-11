"""Chart rendering and PDF assembly."""

from finagent.services import charts, report


def test_each_chart_renders_a_png(startup_record):
    for _caption, png in charts.all_charts(startup_record):
        assert png[:8] == b"\x89PNG\r\n\x1a\n", "expected a PNG signature"
        assert len(png) > 1000


def test_report_includes_three_charts(startup_record):
    assert len(charts.all_charts(startup_record)) == 3


def test_builds_a_pdf(startup_record):
    pdf = report.build_pdf(startup_record, "## Executive Summary\nLooks promising.")
    assert pdf[:5] == b"%PDF-", "expected a PDF header"
    assert len(pdf) > 10_000, "a report with three charts should not be tiny"


def test_verified_startup_pdf_is_larger(startup_record, verified_record):
    """The verified variant adds four registry rows to the profile table."""
    plain = report.build_pdf(startup_record, "## Summary\nText.")
    verified = report.build_pdf(verified_record, "## Summary\nText.")
    assert len(verified) > len(plain)


def test_markdown_headings_bullets_and_bold_are_converted():
    from finagent.services.report import _markdown_flowables, _styles

    flowables = _markdown_flowables(
        "## Heading\n- first bullet\n- second bullet\n**Bold line**\nPlain body text.\n",
        _styles(),
    )
    assert len(flowables) >= 5


def test_strips_inline_markdown():
    from finagent.services.report import _strip_markdown

    assert _strip_markdown("**bold** and *italic*") == "bold and italic"


def test_filename_is_slugged(startup_record):
    name = report.filename_for(startup_record)
    assert name.startswith("report_QuantumFleet_AI_")
    assert name.endswith(".pdf")
    assert " " not in name
