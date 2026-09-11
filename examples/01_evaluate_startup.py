#!/usr/bin/env python3
"""End-to-end startup evaluation.

Registers a startup, uploads its pitch deck, verifies it against the company
registry, then runs the LangGraph pipeline and saves the investor PDF.

    python examples/01_evaluate_startup.py
    python examples/01_evaluate_startup.py --deck dataset/sample_pitch_deck.pdf
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests

DEFAULT_BASE_URL = "http://localhost:7860"
SANDBOX_ACTIVE_CIN = "U72900MH2021PTC123456"

STARTUP = {
    "name": "QuantumFleet AI",
    "domain": "Logistics AI",
    "description": (
        "Route optimisation for mid-size freight fleets. Cuts empty-mile "
        "running by re-planning loads against live traffic and order data."
    ),
    "team": (
        "Two ex-Flipkart supply-chain engineers and an operations lead who ran "
        "a 200-truck regional fleet."
    ),
    "extras": "Stage: Seed. Team size: 6. Raising $500k. 4 paying pilots.",
}


def show(label: str, payload: object) -> None:
    print(f"\n=== {label} ===")
    print(json.dumps(payload, indent=2)[:1200])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--deck", type=Path, help="Optional PDF/DOCX to upload")
    parser.add_argument("--out", type=Path, default=Path("evaluation_report.pdf"))
    args = parser.parse_args()

    base = args.base_url.rstrip("/")

    # 1 ── Register ───────────────────────────────────────────────────────────
    response = requests.post(f"{base}/startups", json=STARTUP, timeout=30)
    response.raise_for_status()
    startup = response.json()
    startup_id = startup["startup_id"]
    show("1. Registered", startup)

    # 2 ── Upload a deck (optional; the pipeline runs without one) ────────────
    if args.deck and args.deck.exists():
        with args.deck.open("rb") as handle:
            upload = requests.post(
                f"{base}/api/startups/{startup_id}/documents/upload",
                files={"documents": (args.deck.name, handle, "application/pdf")},
                timeout=180,
            )
        show("2. Document ingested", upload.json())
    else:
        print("\n=== 2. Document ingested ===\nskipped (no --deck given)")

    # 3 ── Verify against the registry ────────────────────────────────────────
    verify = requests.post(
        f"{base}/startups/{startup_id}/verify/mca",
        json={"cin": SANDBOX_ACTIVE_CIN},
        timeout=30,
    )
    # A non-active company returns 400 — that is a result, not a crash.
    show("3. Registry verification", verify.json())

    # 4 ── Run the pipeline and save the PDF ──────────────────────────────────
    print("\n=== 4. Running the evaluation pipeline (this takes 30-90s) ===")
    report = requests.post(f"{base}/reports/{startup_id}", timeout=600)
    if report.status_code != 200:
        print(f"Report generation failed: {report.status_code} {report.text[:400]}")
        return 1

    args.out.write_bytes(report.content)
    print(f"Saved {len(report.content):,} bytes to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
