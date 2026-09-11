"""Central configuration.

Every environment variable the service reads is declared here exactly once so
that configuration is discoverable and testable. Import ``settings`` rather than
calling ``os.getenv`` from feature code.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _hf_cache_dirs() -> dict[str, str]:
    """Cache locations for HuggingFace artefacts.

    Containers frequently run as a non-root user without a writable ``$HOME``,
    so the caches are pinned to the system temp directory.
    """
    tmp = tempfile.gettempdir()
    return {
        "TRANSFORMERS_CACHE": os.path.join(tmp, "transformers_cache"),
        "HF_HOME": os.path.join(tmp, "hf_home"),
        "HUGGINGFACE_HUB_CACHE": os.path.join(tmp, "hf_hub_cache"),
        "SENTENCE_TRANSFORMERS_HOME": os.path.join(tmp, "sentence_transformers"),
    }


@dataclass(frozen=True)
class Settings:
    """Immutable snapshot of the process configuration."""

    # ── LLM ───────────────────────────────────────────────────────────────
    groq_api_key: str = field(default_factory=lambda: _env("GROQ_API_KEY"))
    llm_model: str = field(
        default_factory=lambda: _env("LLM_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
    )

    # ── Vector store ──────────────────────────────────────────────────────
    qdrant_url: str = field(default_factory=lambda: _env("QDRANT_URL"))
    qdrant_api_key: str = field(default_factory=lambda: _env("QDRANT_API_KEY"))
    embedding_model: str = field(
        default_factory=lambda: _env("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    )
    embedding_dim: int = 384

    # ── Registry verification (MCA) ───────────────────────────────────────
    mca_api_key: str = field(default_factory=lambda: _env("MCA_API_KEY"))
    mca_api_url: str = field(
        default_factory=lambda: _env("MCA_API_URL", "https://api.karza.in/v3/company-master")
    )

    # ── Market data ───────────────────────────────────────────────────────
    rapidapi_key: str = field(default_factory=lambda: _env("RAPIDAPI_KEY"))
    rapidapi_host: str = "real-time-finance-data.p.rapidapi.com"
    rapidapi_base_url: str = "https://real-time-finance-data.p.rapidapi.com"
    news_cache_ttl_seconds: int = 300

    # ── Retrieval / chunking ──────────────────────────────────────────────
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_top_k: int = 6

    # ── Workflow limits ───────────────────────────────────────────────────
    max_query_rewrites: int = 2
    recursion_limit: int = 15

    # ── Server ────────────────────────────────────────────────────────────
    host: str = field(default_factory=lambda: _env("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(_env("PORT", "7860")))
    log_level: str = field(default_factory=lambda: _env("LOG_LEVEL", "INFO"))

    @property
    def qdrant_enabled(self) -> bool:
        return bool(self.qdrant_url)

    @property
    def mca_live(self) -> bool:
        """False means the deterministic sandbox provider is used."""
        return bool(self.mca_api_key)

    @property
    def market_data_enabled(self) -> bool:
        return bool(self.rapidapi_key)


def configure_hf_cache() -> str:
    """Create and export the HuggingFace cache directories.

    Returns the sentence-transformers cache path, which the embedding loader
    passes explicitly to ``HuggingFaceEmbeddings``.
    """
    dirs = _hf_cache_dirs()
    for path in dirs.values():
        os.makedirs(path, exist_ok=True)
    os.environ.update(dirs)
    return dirs["SENTENCE_TRANSFORMERS_HOME"]


settings = Settings()
