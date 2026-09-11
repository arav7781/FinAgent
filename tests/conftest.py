"""Shared test fixtures.

The suite runs without a Groq key, a vector database, or network access. A
``GROQ_API_KEY`` placeholder is set before any import so ``settings`` builds
cleanly, and the LLM is stubbed wherever a test exercises a model path.
"""

from __future__ import annotations

import os
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

os.environ.setdefault("GROQ_API_KEY", "test-key-not-used")
os.environ.setdefault("LOG_LEVEL", "WARNING")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finagent import store  # noqa: E402
from finagent.services import mca  # noqa: E402


@pytest.fixture(autouse=True)
def clean_store():
    """Every test starts against an empty store."""
    store.reset()
    yield
    store.reset()


@pytest.fixture
def startup_record() -> dict[str, Any]:
    """A registered startup with no verification yet."""
    return {
        "startup_id": "11111111-2222-3333-4444-555555555555",
        "name": "QuantumFleet AI",
        "domain": "Logistics AI",
        "description": "Route optimisation for mid-size freight fleets.",
        "team": "Two ex-Flipkart engineers and one operations lead.",
        "extras": "Stage: Seed, Team Size: 6",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "document_collections": [],
        "extracted_text": "",
        "verification": mca.empty_verification(),
    }


@pytest.fixture
def verified_record(startup_record) -> dict[str, Any]:
    """The same startup, verified against the sandbox registry.

    Deep-copied so a test can hold both the verified and unverified variants
    and compare them.
    """
    record = deepcopy(startup_record)
    mca.apply_result(
        record,
        "U72900MH2021PTC123456",
        mca.sandbox_response("U72900MH2021PTC123456"),
    )
    return record


class StubLLM:
    """Minimal stand-in for a chat model.

    ``invoke`` returns a canned response and records what it was asked, so tests
    can assert on prompt construction without a network call.
    """

    def __init__(self, reply: str = "yes"):
        self.reply = reply
        self.calls: list = []

    def invoke(self, messages, **_):
        self.calls.append(messages)

        class _Response:
            content = self.reply

        return _Response()

    def bind_tools(self, _tools):
        return self


@pytest.fixture
def stub_llm(monkeypatch):
    """Install a StubLLM as the process-wide model."""
    from finagent.services import runtime

    stub = StubLLM()
    monkeypatch.setattr(runtime, "_llm", stub, raising=False)
    monkeypatch.setattr(runtime, "get_llm", lambda: stub)
    monkeypatch.setattr(runtime, "build_llm", lambda **_: stub)
    return stub


@pytest.fixture
def client():
    """A TestClient over the bare FastAPI app (no lifespan, no Socket.IO)."""
    from fastapi.testclient import TestClient

    from finagent.app import api

    return TestClient(api)
