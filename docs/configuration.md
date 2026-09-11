# Configuration

Every environment variable is declared once, in
[`src/finagent/settings.py`](../src/finagent/settings.py). Feature code imports
`settings` rather than calling `os.getenv`, so configuration is discoverable and
testable.

```bash
cp .env.example .env
```

## Variables

| Variable | Required | Default | Without it |
| :--- | :---: | :--- | :--- |
| `GROQ_API_KEY` | **yes** | — | No agent can run. |
| `QDRANT_URL` | no | — | Retrieval falls back to in-memory document text. |
| `QDRANT_API_KEY` | no | — | Only needed for Qdrant Cloud. |
| `RAPIDAPI_KEY` | no | — | News Reporter uses model knowledge; headlines endpoint returns `[]`. |
| `MCA_API_KEY` | no | — | The deterministic sandbox registry answers. |
| `MCA_API_URL` | no | Karza company-master | Provider endpoint. |
| `LLM_MODEL` | no | `meta-llama/llama-4-scout-17b-16e-instruct` | — |
| `EMBEDDING_MODEL` | no | `sentence-transformers/all-MiniLM-L6-v2` | — |
| `HOST` | no | `0.0.0.0` | — |
| `PORT` | no | `7860` | — |
| `LOG_LEVEL` | no | `INFO` | `DEBUG` logs full prompts. |

## Tunables

These are code constants rather than environment variables, because changing
them changes behaviour in ways that deserve a commit. They are documented in
`config/app.defaults.yaml` and defined in `settings.py`.

| Setting | Default | Raise it when |
| :--- | :--- | :--- |
| `chunk_size` | 1000 | Documents have long, self-contained sections. |
| `chunk_overlap` | 200 | Claims are being split across chunk boundaries. |
| `retrieval_top_k` | 6 | Reports miss detail that is in the deck. |
| `max_query_rewrites` | 2 | Thin-evidence reports matter more than latency. |
| `recursion_limit` | 15 | You raised `max_query_rewrites`. Keep it above `2 × rewrites + 3`. |
| `news_cache_ttl_seconds` | 300 | You are hitting RapidAPI rate limits. |

If you change the embedding model, update `embedding_dim` to match — Qdrant
collections are created with a fixed vector size, and an existing collection
must be recreated.

## Changing the model

`LLM_MODEL` accepts any chat model Groq serves. The evaluation pipeline needs
tool calling; a model without it will still produce a report, but the analyst
will never search the web.

## `config/`

Non-secret runtime configuration, checked in:

| File | |
| :--- | :--- |
| `logging.yaml` | Levels and handlers, including the Socket.IO stream handler. |
| `app.defaults.yaml` | The tunables above, documented in one place. |
| `scoring_rubric.yaml` | The six evaluation dimensions, their weights, and the recommendation bands. |

`settings.py` remains the source of truth at runtime; these files document the
values and are the template for a `dictConfig`-based setup.

## Secrets

`.env` is gitignored. Never commit real keys — `.env.example` carries
placeholders and is the file that belongs in version control. In production,
inject the environment from your platform's secret manager rather than shipping
a `.env` inside the image.
