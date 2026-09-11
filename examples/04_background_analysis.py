#!/usr/bin/env python3
"""Fire-and-poll analysis.

A full evaluation takes longer than a browser request should stay open, so a UI
starts the run and polls for structured sections instead of waiting on a PDF.

    python examples/04_background_analysis.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time

import requests

DEFAULT_BASE_URL = "http://localhost:7860"
POLL_INTERVAL_SECONDS = 5
POLL_TIMEOUT_SECONDS = 300

STARTUP = {
    "name": "LedgerLoom",
    "domain": "Fintech / SME accounting",
    "description": "Automated bank reconciliation for small businesses in India.",
    "team": "Three founders: a chartered accountant and two backend engineers.",
    "extras": "Stage: Pre-seed. 40 unpaid beta users.",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    startup_id = requests.post(f"{base}/startups", json=STARTUP, timeout=30).json()["startup_id"]
    print(f"Registered {STARTUP['name']} as {startup_id}")

    requests.post(f"{base}/api/startups/{startup_id}/analyze", timeout=30).raise_for_status()
    print("Analysis started; polling for completion...")

    deadline = time.time() + POLL_TIMEOUT_SECONDS
    while time.time() < deadline:
        status = requests.get(
            f"{base}/api/startups/{startup_id}/report/status", timeout=30
        ).json()

        if status["status"] == "complete":
            print("\n=== Parsed sections ===")
            print(json.dumps(status["analysis"], indent=2)[:2000])
            return 0
        if status["status"] == "failed":
            print(f"Analysis failed: {status.get('error')}")
            return 1

        print(f"  status={status['status']}")
        time.sleep(POLL_INTERVAL_SECONDS)

    print("Timed out waiting for the analysis to finish.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
