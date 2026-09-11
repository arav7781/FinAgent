# config/

Runtime configuration that is not secret.

| File | Purpose |
| :--- | :--- |
| `logging.yaml` | Logging levels and handlers, including the Socket.IO stream handler. |
| `app.defaults.yaml` | Tunable defaults — chunking, retrieval depth, workflow limits. |
| `scoring_rubric.yaml` | The six evaluation dimensions and their weights. |

Secrets never live here. They come from the environment — copy `.env.example`
to `.env` and fill it in. Every variable the service reads is declared once in
[`src/finagent/settings.py`](../src/finagent/settings.py).

These YAML files document the values the code currently uses; `settings.py`
remains the single source of truth at runtime.
