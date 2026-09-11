"""FinAgent — an AI-assisted startup evaluation and financial advisory backend.

The package is organised in four layers:

``finagent.api``
    FastAPI routers. HTTP concerns only — validation, status codes, responses.
``finagent.agents``
    LangGraph workflows, prompts, tools and guardrails.
``finagent.services``
    Stateless capability providers: documents, vector store, MCA registry,
    market data, charts, PDF rendering and the shared LLM factory.
``finagent.store``
    The in-memory repositories the API and agents share.
"""

__version__ = "3.0.0"
__all__ = ["__version__"]
