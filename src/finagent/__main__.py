"""``python -m finagent`` — run the development server."""

from __future__ import annotations

import uvicorn

from finagent.settings import settings


def main() -> None:
    uvicorn.run(
        "finagent.app:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
