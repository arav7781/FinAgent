# FinAgent Documentation

| Document | Read it for |
| :--- | :--- |
| [architecture.md](architecture.md) | How the system is put together and why it is split this way. |
| [agents.md](agents.md) | The two LangGraph workflows, node by node. |
| [api-reference.md](api-reference.md) | Every endpoint, with request and response shapes. |
| [configuration.md](configuration.md) | Environment variables and what happens when each is missing. |
| [deployment.md](deployment.md) | Docker, compose, and running without a container. |
| [testing.md](testing.md) | What the suite covers and how to extend it. |
| [diagrams/](diagrams/) | Every figure, and the script that renders them. |

## The project report

The assessed report — need analysis, technical functionality, architecture,
usage and scope, impact — is at
[`report/FinAgent_Report.pdf`](../report/FinAgent_Report.pdf).
It is rebuilt with `make report`.

## Start here

New to the codebase? Read [architecture.md](architecture.md), then follow one
request end to end in [agents.md](agents.md#the-evaluation-workflow). The
fastest way to see the system work is:

```bash
cp .env.example .env      # add your GROQ_API_KEY
make install && make run
python examples/01_evaluate_startup.py
```
