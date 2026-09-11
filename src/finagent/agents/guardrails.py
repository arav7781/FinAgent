"""Input guardrails for the advisory chat.

A deterministic pattern filter runs before any model call. It is cheap, cannot
itself be talked out of a decision, and covers the two categories that matter
for a finance assistant: attempts to overwrite the system instructions, and
requests for content the assistant has no business producing.

This is a first line of defence, not a complete safety system — the subagent
prompts constrain behaviour further.
"""

from __future__ import annotations

import re
from re import Pattern

BLOCK_PATTERNS: list[Pattern[str]] = [
    # Prompt-injection / instruction override
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?)", re.I),
    re.compile(r"(system|developer)\s+prompt", re.I),
    re.compile(r"(bypass|override|disable)\s+(safety|guardrails|policy|policies|rules)", re.I),
    re.compile(r"jailbreak|dan\s+mode|do\s+anything\s+now", re.I),
    # Role-play into regulated or malicious personas
    re.compile(r"act\s+as\s+(a\s+)?(lawyer|doctor|hacker|jailbroken\s+ai)", re.I),
    # Harmful or off-domain content
    re.compile(
        r"\b(murder|kill|bomb|weapon|hate\s*speech|racist|sexist|porn|sex\s*chat|explicit)\b",
        re.I,
    ),
]

REFUSAL_MESSAGE = (
    "Request blocked by safety policy. Ask a finance-focused question without "
    "jailbreak or harmful instructions."
)


def matched_pattern(text: str) -> str | None:
    """Return the offending substring, or ``None`` when the input is clean."""
    candidate = (text or "").strip()
    if not candidate:
        return None
    for pattern in BLOCK_PATTERNS:
        found = pattern.search(candidate)
        if found:
            return found.group(0)
    return None


def is_blocked(text: str) -> bool:
    return matched_pattern(text) is not None
