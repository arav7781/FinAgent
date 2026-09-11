"""Matplotlib figures embedded in the investor PDF.

All three charts share one palette and are rendered head-less to PNG bytes so
they can be streamed straight into ReportLab without touching the filesystem.
"""

from __future__ import annotations

import io
from collections.abc import Sequence

import matplotlib

matplotlib.use("Agg")  # no display server in a container
import matplotlib.pyplot as plt  # noqa: E402

# ─── Palette ──────────────────────────────────────────────────────────────────

FIGURE_BG = "#0f172a"
AXES_BG = "#1e293b"
GRID_COLOR = "#334155"
MUTED = "#94a3b8"
ACCENT = "#6366f1"
ACCENT_LIGHT = "#a78bfa"
SERIES_COLORS = ["#6366f1", "#8b5cf6", "#a78bfa", "#7c3aed", "#9333ea", "#c084fc"]

FIGSIZE = (7, 4)
DPI = 150

# Scorecard dimensions. Scores are the platform's current heuristic baseline;
# swapping in model-derived scores means changing this one mapping.
SCORECARD: dict[str, float] = {
    "Product\nStrength": 7.8,
    "Market\nSize": 8.2,
    "Team\nQuality": 7.0,
    "Business\nModel": 7.5,
    "Competitive\nMoat": 6.8,
    "Execution\nRisk": 7.2,
}

MARKET_SPLIT: list[tuple[str, int]] = [
    ("TAM\n(Total Market)", 100),
    ("SAM\n(Serviceable)", 30),
    ("SOM\n(Obtainable)", 8),
]

TREND_YEARS: Sequence[int] = (2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028)
TREND_VALUES: Sequence[int] = (12, 18, 26, 38, 54, 72, 97, 130)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _new_axes():
    fig, ax = plt.subplots(figsize=FIGSIZE, facecolor=FIGURE_BG)
    ax.set_facecolor(AXES_BG)
    return fig, ax


def _style(ax, title: str, xlabel: str = "", ylabel: str = "") -> None:
    ax.set_title(title, color="white", fontsize=13, fontweight="bold", pad=12)
    if xlabel:
        ax.set_xlabel(xlabel, color=MUTED, fontsize=10)
    if ylabel:
        ax.set_ylabel(ylabel, color=MUTED, fontsize=10)
    ax.tick_params(colors=MUTED)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID_COLOR)


def _render(fig) -> bytes:
    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=DPI, bbox_inches="tight", facecolor=FIGURE_BG)
    plt.close(fig)
    buffer.seek(0)
    return buffer.read()


# ─── Charts ───────────────────────────────────────────────────────────────────

def market_opportunity_chart(startup: dict) -> bytes:
    """TAM / SAM / SOM funnel as a labelled bar chart."""
    fig, ax = _new_axes()
    labels = [label for label, _ in MARKET_SPLIT]
    values = [value for _, value in MARKET_SPLIT]

    bars = ax.bar(labels, values, color=SERIES_COLORS[:3], width=0.5,
                  edgecolor=GRID_COLOR, linewidth=0.8)
    for bar, value in zip(bars, values, strict=True):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                f"${value}B", ha="center", va="bottom",
                color="white", fontsize=11, fontweight="bold")

    ax.set_ylim(0, 130)
    _style(ax, f"Market Opportunity — {startup.get('domain', 'Industry')}",
           ylabel="Market Size (USD Billions)")
    return _render(fig)


def evaluation_scorecard_chart(startup: dict) -> bytes:
    """Horizontal score bars across the six evaluation dimensions."""
    fig, ax = _new_axes()
    dimensions = list(SCORECARD.keys())
    scores = list(SCORECARD.values())

    bars = ax.barh(dimensions, scores, color=SERIES_COLORS,
                   edgecolor=GRID_COLOR, linewidth=0.8, height=0.6)
    for bar, score in zip(bars, scores, strict=True):
        ax.text(score + 0.1, bar.get_y() + bar.get_height() / 2, f"{score}/10",
                va="center", color="white", fontsize=9, fontweight="bold")

    ax.set_xlim(0, 11)
    _style(ax, f"AI Evaluation Scorecard — {startup.get('name', 'Startup')}",
           xlabel="Score (out of 10)")
    return _render(fig)


def market_trend_chart(startup: dict) -> bytes:
    """Historical and projected market size as a filled trend line."""
    fig, ax = _new_axes()
    ax.plot(TREND_YEARS, TREND_VALUES, color=ACCENT, linewidth=2.5, marker="o",
            markersize=7, markerfacecolor=ACCENT_LIGHT, markeredgecolor=ACCENT)
    ax.fill_between(TREND_YEARS, TREND_VALUES, alpha=0.15, color=ACCENT)

    # Label every other point so the line stays readable.
    for year, value in zip(TREND_YEARS[::2], TREND_VALUES[::2], strict=True):
        ax.annotate(f"${value}B", (year, value), textcoords="offset points",
                    xytext=(0, 10), ha="center", color=ACCENT_LIGHT, fontsize=8)

    _style(ax, f"Market Growth Trend — {startup.get('domain', 'Industry')}",
           xlabel="Year", ylabel="Market Size (USD Billions)")
    return _render(fig)


def all_charts(startup: dict) -> list[tuple[str, bytes]]:
    """Every chart in the order the report presents them."""
    return [
        ("Market Opportunity (TAM / SAM / SOM)", market_opportunity_chart(startup)),
        ("Market Growth Trend (2021–2028)", market_trend_chart(startup)),
        ("AI Evaluation Scorecard", evaluation_scorecard_chart(startup)),
    ]
