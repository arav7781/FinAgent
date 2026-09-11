"""Long-lived clients shared across requests.

Loading an embedding model or a Docling converter costs seconds, so they are
built once during application startup and read from here. Every getter returns
``None`` when the dependency is unavailable, and callers degrade rather than
crash — a missing Qdrant should not take the whole service down.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from finagent.settings import configure_hf_cache, settings

logger = logging.getLogger(__name__)

_llm: Any | None = None
_embeddings: Any | None = None
_qdrant: Any | None = None
_converter: Any | None = None


# ─── Accessors ────────────────────────────────────────────────────────────────

def get_llm() -> Any | None:
    return _llm


def get_embeddings() -> Any | None:
    return _embeddings


def get_qdrant() -> Any | None:
    return _qdrant


def get_converter() -> Any | None:
    return _converter


def status() -> dict:
    """Readiness of each dependency, surfaced by ``GET /health``."""
    return {
        "llm_ready": _llm is not None,
        "embeddings_ready": _embeddings is not None,
        "qdrant_connected": _qdrant is not None,
        "docling_ready": _converter is not None,
    }


# ─── Builders ─────────────────────────────────────────────────────────────────

def build_llm(temperature: float = 0.2, max_tokens: int = 2048):
    """Create a Groq chat model.

    A new instance per call keeps temperature and token budget local to the
    caller — the analyst agent wants determinism, the educator wants variety.
    """
    from langchain_groq import ChatGroq

    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not set")
    return ChatGroq(
        groq_api_key=settings.groq_api_key,
        model_name=settings.llm_model,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def _connect_qdrant():
    from qdrant_client import QdrantClient

    client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        timeout=60,
        verify=False,
        check_compatibility=False,
    )
    client.get_collections()  # fail fast if the URL or key is wrong
    return client


def _load_embeddings(cache_dir: str):
    """Load the sentence-transformer, trying the hub id then the bare name."""
    from langchain_huggingface import HuggingFaceEmbeddings

    candidates = [settings.embedding_model, settings.embedding_model.split("/")[-1]]
    for model_name in candidates:
        try:
            model = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={"device": "cpu"},
                cache_folder=cache_dir,
            )
            logger.info("Embeddings initialised: %s", model_name)
            return model
        except Exception as exc:
            logger.warning("Embeddings init failed for %s: %s", model_name, exc)
    raise RuntimeError(
        "All embedding models failed to load. Is 'sentence-transformers' installed?"
    )


async def startup() -> None:
    """Initialise every dependency. Only the LLM is mandatory."""
    global _llm, _embeddings, _qdrant, _converter

    cache_dir = configure_hf_cache()

    if settings.qdrant_enabled:
        try:
            _qdrant = await asyncio.to_thread(_connect_qdrant)
            logger.info("Qdrant connected")
        except Exception as exc:
            logger.warning("Qdrant unavailable (%s) — falling back to in-memory text", exc)
    else:
        logger.info("QDRANT_URL not set — retrieval uses the in-memory fallback")

    try:
        _embeddings = await asyncio.to_thread(_load_embeddings, cache_dir)
    except Exception as exc:
        logger.warning("Embeddings unavailable (%s) — semantic search disabled", exc)

    _llm = build_llm()
    logger.info("LLM ready: %s", settings.llm_model)

    try:
        from docling.document_converter import DocumentConverter

        _converter = await asyncio.to_thread(DocumentConverter)
        logger.info("Docling converter ready")
    except Exception as exc:
        logger.warning("Docling unavailable (%s) — using PyPDF2/pdfplumber only", exc)


async def shutdown() -> None:
    global _llm, _embeddings, _qdrant, _converter
    _llm = _embeddings = _qdrant = _converter = None
