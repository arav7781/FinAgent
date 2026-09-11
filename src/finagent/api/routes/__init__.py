"""FastAPI routers, one module per resource."""

from finagent.api.routes import (
    chat,
    documents,
    finscope,
    health,
    reports,
    startups,
    verification,
)

ROUTERS = [
    startups.router,
    documents.router,
    reports.router,
    verification.router,
    chat.router,
    finscope.router,
    health.router,
]

__all__ = ["ROUTERS"]
