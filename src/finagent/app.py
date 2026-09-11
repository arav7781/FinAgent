"""Application assembly.

``app`` is the ASGI callable uvicorn serves: the FastAPI application wrapped in
a Socket.IO server so REST and the ``/socket.io`` log stream share one port.
Import ``api`` instead if you want the bare FastAPI app (the test suite does).
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from finagent import __version__, realtime
from finagent.api.routes import ROUTERS
from finagent.services import runtime
from finagent.settings import settings

logger = logging.getLogger(__name__)

DESCRIPTION = """
FinAgent is an AI evaluation and advisory backend for early-stage investment.

* **Startup evaluation** — a LangGraph agent researches a startup, retrieves its
  documents, verifies it against the company registry, and renders an
  investor-ready PDF with charts.
* **FinScope advisory** — an intent router that sends a question to one of five
  specialist subagents: education, document analysis, market research, portfolio
  coaching, or live news.
"""


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(levelname)s:%(name)s:%(message)s",
    )
    realtime.install_log_handler()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Build shared clients on startup, release them on shutdown."""
    realtime.bind_loop(asyncio.get_running_loop())
    await runtime.startup()
    logger.info("FinAgent %s initialised", __version__)
    yield
    await runtime.shutdown()
    realtime.bind_loop(None)
    logger.info("FinAgent shutting down")


def create_app() -> FastAPI:
    """Build the FastAPI application."""
    application = FastAPI(
        title="FinAgent",
        description=DESCRIPTION,
        version=__version__,
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for router in ROUTERS:
        application.include_router(router)

    return application


configure_logging()

api = create_app()

# ASGI entrypoint: Socket.IO in front, FastAPI behind.
app = socketio.ASGIApp(realtime.sio, api)
