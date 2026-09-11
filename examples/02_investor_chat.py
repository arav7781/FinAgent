#!/usr/bin/env python3
"""Investor Q&A against a registered startup.

Asks a series of due-diligence questions. Answers are grounded in the startup's
profile and any documents it has, so the assistant says "not stated" rather than
guessing.

    python examples/02_investor_chat.py --name "QuantumFleet AI"
"""

from __future__ import annotations

import argparse
import sys

import requests

DEFAULT_BASE_URL = "http://localhost:7860"

QUESTIONS = [
    "What problem does this startup solve, and for whom?",
    "What is the team's relevant experience?",
    "What traction has been demonstrated so far?",
    "What are the three biggest risks for an investor?",
    "Is the company verified against the company registry?",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--name", default="QuantumFleet AI",
                        help="Startup name (registered via example 01)")
    parser.add_argument("--id", help="Startup UUID; overrides --name")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    endpoint = (
        f"{base}/chat/{args.id}" if args.id
        else f"{base}/chat/by-name/{requests.utils.quote(args.name)}"
    )

    for question in QUESTIONS:
        print(f"\nQ: {question}")
        response = requests.post(endpoint, json={"question": question}, timeout=120)
        if response.status_code == 404:
            print("Startup not found. Run examples/01_evaluate_startup.py first.")
            return 1
        response.raise_for_status()
        print(f"A: {response.json()['answer']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
