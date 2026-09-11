"""Qdrant-backed semantic retrieval.

Both writes and reads degrade gracefully. If Qdrant or the embedding model is
missing, :func:`store_chunks` reports that nothing was indexed and
:func:`retrieve` returns an empty string — the caller then falls back to the
raw extracted text held on the startup record.
"""

from __future__ import annotations

import logging

from finagent.services import runtime
from finagent.settings import settings

logger = logging.getLogger(__name__)

UPSERT_BATCH_SIZE = 100


class VectorStoreUnavailable(Exception):
    """Raised when an operation needs Qdrant but it is not connected."""


def available() -> bool:
    return runtime.get_qdrant() is not None and runtime.get_embeddings() is not None


def _ensure_collection(client, collection_name: str) -> None:
    from qdrant_client.http.models import Distance, VectorParams

    try:
        client.get_collection(collection_name)
    except Exception:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=settings.embedding_dim, distance=Distance.COSINE
            ),
        )
        logger.info("Created Qdrant collection '%s'", collection_name)


def store_chunks(documents: list, collection_name: str) -> int:
    """Embed and upsert chunks. Returns the number of points written."""
    from qdrant_client.http.models import PointStruct

    client = runtime.get_qdrant()
    embeddings = runtime.get_embeddings()
    if client is None or embeddings is None:
        raise VectorStoreUnavailable("Qdrant or the embedding model is unavailable")

    _ensure_collection(client, collection_name)

    # Offset new ids past the existing count so repeat uploads append rather
    # than overwrite earlier chunks.
    offset = client.count(collection_name=collection_name).count
    points = [
        PointStruct(
            id=offset + index,
            vector=embeddings.embed_query(doc.page_content),
            payload={"text": doc.page_content, "metadata": doc.metadata},
        )
        for index, doc in enumerate(documents)
    ]

    for start in range(0, len(points), UPSERT_BATCH_SIZE):
        client.upsert(
            collection_name=collection_name,
            points=points[start : start + UPSERT_BATCH_SIZE],
        )

    logger.info("Stored %d chunks in collection '%s'", len(points), collection_name)
    return len(points)


def retrieve(query: str, collection_name: str, top_k: int | None = None) -> str:
    """Return the most similar chunks joined into one context block.

    An empty string means "nothing usable" for any reason — no collection, no
    client, no hits — so callers need only one fallback branch.
    """
    client = runtime.get_qdrant()
    embeddings = runtime.get_embeddings()
    if client is None or embeddings is None or not collection_name:
        return ""

    try:
        client.get_collection(collection_name)
    except Exception:
        logger.info("Collection '%s' does not exist yet", collection_name)
        return ""

    try:
        hits = client.search(
            collection_name=collection_name,
            query_vector=embeddings.embed_query(query),
            limit=top_k or settings.retrieval_top_k,
        )
    except Exception as exc:
        logger.error("Retrieval failed for '%s': %s", collection_name, exc)
        return ""

    return "\n\n---\n\n".join(hit.payload["text"] for hit in hits) if hits else ""
