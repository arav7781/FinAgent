"""Socket.IO log streaming.

The agent workflows are long-running and opaque from the outside, so every log
record is mirrored to connected clients on the ``log_stream`` channel. This lets
a UI show what the analyst agent is doing while a report is being built.
"""

from __future__ import annotations

import asyncio
import logging

import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

# Set during application startup; the log handler needs a running loop to
# schedule emits from non-async threads.
_loop: asyncio.AbstractEventLoop | None = None


class SocketIOLogHandler(logging.Handler):
    """Forwards log records to Socket.IO clients.

    Emitting must never break the caller, so every failure is swallowed — a
    dropped log line is preferable to a failed analysis run.
    """

    def emit(self, record: logging.LogRecord) -> None:
        if _loop is None or not _loop.is_running():
            return
        try:
            message = self.format(record)
            asyncio.run_coroutine_threadsafe(
                sio.emit("log_stream", {"message": message}), _loop
            )
        except Exception:  # pragma: no cover - defensive
            pass


def bind_loop(loop: asyncio.AbstractEventLoop | None) -> None:
    """Attach (or detach, with ``None``) the event loop used for emits."""
    global _loop
    _loop = loop


async def broadcast(message: str) -> None:
    """Push a one-off status line to connected clients."""
    try:
        await sio.emit("log_stream", {"message": message})
    except Exception:  # pragma: no cover - defensive
        pass


def install_log_handler(level: int = logging.INFO) -> SocketIOLogHandler:
    """Register the streaming handler on the root logger."""
    handler = SocketIOLogHandler()
    handler.setFormatter(logging.Formatter("INFO:%(name)s:%(message)s"))
    handler.setLevel(level)
    logging.getLogger().addHandler(handler)
    return handler
