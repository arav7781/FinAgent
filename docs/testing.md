# Testing

```bash
make dev      # installs requirements-dev.txt
make test     # PYTHONPATH=src pytest -q
make lint     # ruff check src tests
```

125 tests, no network, no API key, no vector database. A placeholder
`GROQ_API_KEY` is set in `conftest.py` before any import so `settings` builds,
and the model is stubbed wherever a test exercises a model path.

## Coverage

| File | What it pins down |
| :--- | :--- |
| `test_api.py` | HTTP contract: status codes, validation, 404s, the guardrail 400. |
| `test_mca.py` | CIN validation, sandbox lookup, every consistency flag. |
| `test_agents.py` | Intent routing, the rewrite budget, grader failure handling. |
| `test_report.py` | Charts render as PNG, the PDF assembles, Markdown converts. |
| `test_documents.py` | Chunking, overlap, extractor fallback order, suffix detection. |
| `test_startups_service.py` | Record construction, legacy aliases, section parsing. |
| `test_store.py` | Repository semantics, including newest-wins name lookup. |
| `test_market_data.py` | Symbol resolution and the news cache. |
| `test_settings.py` | Defaults and the derived integration flags. |

## Fixtures

| Fixture | |
| :--- | :--- |
| `client` | `TestClient` over the bare FastAPI app — no lifespan, so nothing is initialised. That is the point: these tests prove which endpoints work with every optional dependency down. |
| `startup_record` | A registered startup, unverified. |
| `verified_record` | The same startup, verified against the sandbox. Deep-copied, so a test can hold both and compare. |
| `stub_llm` | A fake model that returns a canned reply and records its prompts. |
| `clean_store` | Autouse; resets the in-memory store around every test. |

## What is deliberately not tested

Live calls to Groq, Qdrant, RapidAPI and DuckDuckGo. They are slow,
non-deterministic, and cost money — the seams around them are tested instead
(cache behaviour, fallback paths, error handling). The `examples/` scripts are
the integration check: run them against a live service.

## Adding a test

Put it with the module it covers. If it needs a model, take `stub_llm` rather
than reaching for the network. If it needs an HTTP call, take `client`.

```python
def test_thin_evidence_triggers_a_rewrite(stub_llm):
    stub_llm.reply = "no"
    assert evaluation_graph.grade_relevance(state) == "rewrite"
```

## Data-driven checks

`dataset/` holds fixtures for checks the unit suite cannot make offline:

- `finscope_intents.jsonl` — 30 labelled messages for the intent router.
- `guardrail_probes.jsonl` — prompts that must be blocked, and benign ones that
  must not be.
- `sample_cins.csv` — every CIN path with its expected status code.

`dataset/README.md` has runnable snippets for each.
