"""Document ingestion endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from finagent import store
from finagent.api.deps import require_startup
from finagent.schemas import DocumentUploadRequest, DocumentUploadResponse
from finagent.services import documents, vectorstore
from finagent.services import startups as startup_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Documents"])


async def _ingest(record: dict[str, Any], file_bytes: bytes, suffix: str) -> DocumentUploadResponse:
    """Extract, index, and record a document against a startup.

    The raw text is always kept on the record. Vector indexing is best-effort:
    if Qdrant is down the startup is still analysable from the stored text.
    """
    try:
        chunks = await documents.extract_content(file_bytes, suffix=suffix)
    except documents.DocumentError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    record["extracted_text"] = "\n\n".join(chunk.page_content for chunk in chunks)
    collection_name = store.collection_name_for(record["startup_id"])

    indexed = 0
    try:
        indexed = vectorstore.store_chunks(chunks, collection_name)
        if collection_name not in record["document_collections"]:
            record["document_collections"].append(collection_name)
    except vectorstore.VectorStoreUnavailable as exc:
        logger.warning("Vector indexing skipped (%s) — using in-memory text", exc)
    except Exception as exc:
        logger.error("Vector indexing failed (%s) — using in-memory text", exc)

    startup_service.apply_update(record, {})
    store.save_startup(record)

    message = (
        f"Document processed and indexed ({indexed} chunks)."
        if indexed
        else f"Document processed ({len(chunks)} chunks held in memory; vector index unavailable)."
    )
    return DocumentUploadResponse(
        status="success",
        startup_id=record["startup_id"],
        collection_name=collection_name if indexed else None,
        chunks_stored=indexed or len(chunks),
        message=message,
    )


@router.post("/startups/{startup_id}/documents", response_model=DocumentUploadResponse,
             summary="Ingest a supporting document from a URL")
async def upload_document_by_url(
    body: DocumentUploadRequest,
    record: dict[str, Any] = Depends(require_startup),
) -> DocumentUploadResponse:
    url = str(body.document_url)
    try:
        file_bytes = documents.download(url)
    except documents.DocumentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return await _ingest(record, file_bytes, documents.suffix_for(url))


@router.post("/api/startups/{startup_id}/documents/upload",
             response_model=DocumentUploadResponse,
             summary="Ingest a supporting document from a multipart upload")
async def upload_document_multipart(
    documents_file: UploadFile = File(..., alias="documents"),
    record: dict[str, Any] = Depends(require_startup),
) -> DocumentUploadResponse:
    file_bytes = await documents_file.read()
    suffix = documents.suffix_for(documents_file.filename or "pitch_deck.pdf")
    return await _ingest(record, file_bytes, suffix)
