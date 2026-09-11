"""Document ingestion.

A pitch deck may be a clean digital PDF, a scanned export, or a DOCX. Rather
than assume one parser is enough, extraction walks a chain of three — Docling
first because it preserves tables and headings as Markdown, then PyPDF2, then
pdfplumber — and accepts the first result with usable text.
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from collections.abc import Callable

import requests

from finagent.services import runtime
from finagent.settings import settings

logger = logging.getLogger(__name__)

MIN_USABLE_CHARS = 10


class DocumentError(Exception):
    """Raised when a document cannot be downloaded or read."""


# ─── Extractors ───────────────────────────────────────────────────────────────

async def _extract_docling(path: str) -> str:
    converter = runtime.get_converter()
    if converter is None:
        return ""
    try:
        result = await asyncio.to_thread(converter.convert, path)
        text = result.document.export_to_markdown()
        if not text or len(text.strip()) < MIN_USABLE_CHARS:
            text = result.document.export_to_text() or ""
        return text
    except Exception as exc:
        logger.warning("Docling extraction failed: %s", exc)
        return ""


async def _extract_pypdf2(path: str) -> str:
    try:
        import PyPDF2

        def _read() -> str:
            with open(path, "rb") as handle:
                reader = PyPDF2.PdfReader(handle)
                return "\n".join(page.extract_text() or "" for page in reader.pages)

        return await asyncio.to_thread(_read)
    except Exception as exc:
        logger.warning("PyPDF2 extraction failed: %s", exc)
        return ""


async def _extract_pdfplumber(path: str) -> str:
    try:
        import pdfplumber

        def _read() -> str:
            with pdfplumber.open(path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)

        return await asyncio.to_thread(_read)
    except Exception as exc:
        logger.warning("pdfplumber extraction failed: %s", exc)
        return ""


EXTRACTORS: list[Callable] = [_extract_docling, _extract_pypdf2, _extract_pdfplumber]


# ─── Public API ───────────────────────────────────────────────────────────────

def download(url: str, timeout: int = 30) -> bytes:
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.content
    except Exception as exc:
        raise DocumentError(f"Failed to download file: {exc}") from exc


def chunk_text(text: str) -> list:
    """Split raw text into overlapping chunks for embedding.

    The separator order keeps paragraphs together where possible so a chunk
    rarely cuts through the middle of a sentence.
    """
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return [
        Document(page_content=chunk, metadata={"source": "upload", "chunk_id": index})
        for index, chunk in enumerate(splitter.split_text(text))
        if chunk.strip()
    ]


async def extract_content(file_bytes: bytes, suffix: str = ".pdf") -> list:
    """Turn an uploaded file into embeddable chunks.

    Raises :class:`DocumentError` when no extractor produces readable text —
    typically a scanned deck with no OCR layer.
    """
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        text = ""
        for extractor in EXTRACTORS:
            text = await extractor(tmp_path)
            if text and len(text.strip()) > MIN_USABLE_CHARS:
                logger.info("Extracted %d chars via %s", len(text), extractor.__name__)
                break

        if not text or len(text.strip()) <= MIN_USABLE_CHARS:
            raise DocumentError("No readable text found in the uploaded document.")

        return chunk_text(text)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def suffix_for(filename: str, default: str = ".pdf") -> str:
    return os.path.splitext(filename or "")[1].lower() or default
