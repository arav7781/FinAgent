"""Chunking and file-type handling."""

import pytest

from finagent.services import documents
from finagent.settings import settings


def test_chunks_long_text_with_overlap():
    text = ("Revenue grew forty percent year on year. " * 200)
    chunks = documents.chunk_text(text)
    assert len(chunks) > 1
    assert all(chunk.page_content.strip() for chunk in chunks)
    assert all(len(chunk.page_content) <= settings.chunk_size + 100 for chunk in chunks)


def test_chunks_are_indexed_in_order():
    chunks = documents.chunk_text("A paragraph. " * 500)
    assert [c.metadata["chunk_id"] for c in chunks] == list(range(len(chunks)))


def test_short_text_yields_one_chunk():
    assert len(documents.chunk_text("Pre-revenue seed company.")) == 1


def test_empty_text_yields_no_chunks():
    assert documents.chunk_text("") == []


@pytest.mark.parametrize("filename,expected", [
    ("pitch.pdf", ".pdf"),
    ("deck.DOCX", ".docx"),
    ("https://example.com/files/deck.docx", ".docx"),
    ("no_extension", ".pdf"),
    ("", ".pdf"),
])
def test_suffix_detection(filename, expected):
    assert documents.suffix_for(filename) == expected


async def test_unreadable_document_raises(monkeypatch):
    """Every extractor returning nothing must surface a clear error."""
    async def empty(_path):
        return ""

    monkeypatch.setattr(documents, "EXTRACTORS", [empty, empty, empty])
    with pytest.raises(documents.DocumentError, match="No readable text"):
        await documents.extract_content(b"%PDF-1.4 broken", ".pdf")


async def test_first_usable_extractor_wins(monkeypatch):
    calls = []

    async def failing(_path):
        calls.append("failing")
        return ""

    async def working(_path):
        calls.append("working")
        return "Seed-stage logistics AI with $400k ARR. " * 20

    async def never(_path):
        calls.append("never")
        return "should not be reached"

    monkeypatch.setattr(documents, "EXTRACTORS", [failing, working, never])
    chunks = await documents.extract_content(b"data", ".pdf")

    assert chunks
    assert calls == ["failing", "working"], "later extractors must be skipped"
