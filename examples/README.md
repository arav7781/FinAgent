# examples/

Runnable walkthroughs of the two pipelines. Start the API first:

```bash
make run          # http://localhost:7860
```

| Script | What it shows |
| :--- | :--- |
| `01_evaluate_startup.py` | The full evaluation pipeline: register → upload → verify → PDF. |
| `02_investor_chat.py` | Q&A against a registered startup's profile and documents. |
| `03_finscope_chat.py` | Intent routing across all five FinScope subagents. |
| `04_background_analysis.py` | Fire-and-poll analysis for a UI that cannot block. |
| `curl_recipes.sh` | The same calls as plain `curl`, for copy-paste. |

Each script takes `--base-url` (default `http://localhost:7860`) and prints what
it sends and what comes back.

## What you need

`GROQ_API_KEY` is required for anything that calls an agent. Everything else is
optional — without `QDRANT_URL` retrieval falls back to in-memory text, without
`MCA_API_KEY` the sandbox registry answers, and without `RAPIDAPI_KEY` the News
Reporter works from model knowledge instead of live articles.
