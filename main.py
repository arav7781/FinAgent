"""Convenience entrypoint: ``python main.py``.

Kept at the repository root so the service starts the same way it did before
the package restructure. Production deployments should target
``finagent.app:app`` with uvicorn directly — see the Dockerfile.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from finagent.__main__ import main  # noqa: E402

if __name__ == "__main__":
    main()
