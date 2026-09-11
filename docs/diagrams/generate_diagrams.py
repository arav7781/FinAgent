#!/usr/bin/env python3
"""Render every architecture diagram used by the docs and the project report.

Diagrams are drawn with matplotlib rather than a diagram-as-code service so the
repository stays self-contained: `make report` reproduces every figure offline.

    python docs/diagrams/generate_diagrams.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

OUTPUT_DIR = Path(__file__).parent
DPI = 200

# ─── Palette ──────────────────────────────────────────────────────────────────
# Light ground so the figures stay legible in a printed report.

BG = "#ffffff"
INK = "#0f172a"
MUTED = "#64748b"
LINE = "#94a3b8"

INDIGO = "#6366f1"
INDIGO_FILL = "#eef2ff"
VIOLET = "#8b5cf6"
VIOLET_FILL = "#f5f3ff"
TEAL = "#0d9488"
TEAL_FILL = "#f0fdfa"
AMBER = "#d97706"
AMBER_FILL = "#fffbeb"
ROSE = "#e11d48"
ROSE_FILL = "#fff1f2"
SLATE_FILL = "#f8fafc"

FONT = "DejaVu Sans"


# ─── Primitives ───────────────────────────────────────────────────────────────

def new_figure(width: float, height: float):
    fig, ax = plt.subplots(figsize=(width, height), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, label, *, edge=INDIGO, fill=INDIGO_FILL, fontsize=8.5,
        bold=False, radius=1.6, text_color=INK, sublabel=None):
    """A rounded node. Returns (cx, cy) so edges can be anchored to it."""
    ax.add_patch(patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        linewidth=1.3, edgecolor=edge, facecolor=fill,
    ))
    cx, cy = x + w / 2, y + h / 2
    if sublabel:
        ax.text(cx, cy + h * 0.16, label, ha="center", va="center", fontsize=fontsize,
                color=text_color, fontweight="bold" if bold else "normal", family=FONT)
        ax.text(cx, cy - h * 0.22, sublabel, ha="center", va="center",
                fontsize=fontsize - 1.6, color=MUTED, family=FONT)
    else:
        ax.text(cx, cy, label, ha="center", va="center", fontsize=fontsize,
                color=text_color, fontweight="bold" if bold else "normal", family=FONT)
    return cx, cy


def diamond(ax, cx, cy, w, h, label, *, edge=AMBER, fill=AMBER_FILL, fontsize=8):
    ax.add_patch(patches.Polygon(
        [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)],
        closed=True, linewidth=1.3, edgecolor=edge, facecolor=fill,
    ))
    ax.text(cx, cy, label, ha="center", va="center", fontsize=fontsize,
            color=INK, family=FONT)
    return cx, cy


def circle(ax, cx, cy, r, label, *, edge=INK, fill="#ffffff", fontsize=8):
    ax.add_patch(patches.Circle((cx, cy), r, linewidth=1.4,
                                edgecolor=edge, facecolor=fill))
    ax.text(cx, cy, label, ha="center", va="center", fontsize=fontsize,
            color=INK, fontweight="bold", family=FONT)
    return cx, cy


def arrow(ax, start, end, *, label=None, color=LINE, style="-|>", curve=0.0,
          fontsize=7, dashed=False, label_offset=(0, 1.8), label_color=MUTED):
    ax.annotate(
        "", xy=end, xytext=start,
        arrowprops=dict(
            arrowstyle=style, color=color, linewidth=1.2,
            linestyle="--" if dashed else "-",
            connectionstyle=f"arc3,rad={curve}",
            shrinkA=2, shrinkB=2,
        ),
    )
    if label:
        mx = (start[0] + end[0]) / 2 + label_offset[0]
        my = (start[1] + end[1]) / 2 + label_offset[1]
        ax.text(mx, my, label, ha="center", va="center", fontsize=fontsize,
                color=label_color, family=FONT,
                bbox=dict(boxstyle="round,pad=0.22", facecolor=BG, edgecolor="none"))


def band(ax, x, y, w, h, title, *, color=LINE, fill=SLATE_FILL, fontsize=8):
    """A labelled container behind a group of nodes."""
    ax.add_patch(patches.FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0,rounding_size=1.4",
        linewidth=1.0, edgecolor=color, facecolor=fill, linestyle="--", zorder=0,
    ))
    ax.text(x + 1.6, y + h - 2.4, title, ha="left", va="center", fontsize=fontsize,
            color=MUTED, fontweight="bold", family=FONT, zorder=1)


def title(ax, text, subtitle=None):
    ax.text(50, 97, text, ha="center", va="top", fontsize=12.5,
            color=INK, fontweight="bold", family=FONT)
    if subtitle:
        ax.text(50, 92.4, subtitle, ha="center", va="top", fontsize=8.2,
                color=MUTED, family=FONT)


def save(fig, name: str) -> Path:
    path = OUTPUT_DIR / name
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor=BG, pad_inches=0.16)
    plt.close(fig)
    print(f"  wrote {path.relative_to(OUTPUT_DIR.parents[1])}")
    return path


# ─── 1. System architecture ───────────────────────────────────────────────────

def draw_architecture() -> Path:
    fig, ax = new_figure(11, 8)
    title(ax, "FinAgent — System Architecture",
          "Four layers; each depends only on the layer beneath it")

    # Clients
    band(ax, 3, 76, 94, 11, "CLIENTS")
    for label, x in [("Investor dashboard", 7), ("FinScope chat UI", 37), ("curl / scripts", 67)]:
        box(ax, x, 77.5, 25, 5.5, label, edge=MUTED, fill="#ffffff", fontsize=8)

    # API layer
    band(ax, 3, 56, 94, 16, "API LAYER   ·   src/finagent/api")
    for label, x in [("startups", 5), ("documents", 20.3), ("reports", 35.6),
                     ("verification", 50.9), ("chat", 66.2), ("finscope", 81.5)]:
        box(ax, x, 58.5, 13.5, 6.5, label, edge=INDIGO, fill=INDIGO_FILL, fontsize=7.8)
    ax.text(96, 69.6, "FastAPI routers · CORS · Socket.IO log stream",
            ha="right", fontsize=7.4, color=MUTED, family=FONT)

    # Agent layer
    band(ax, 3, 35, 94, 18, "AGENT LAYER   ·   src/finagent/agents")
    box(ax, 6.5, 37.5, 27, 10.5, "Evaluation graph", edge=VIOLET, fill=VIOLET_FILL,
        bold=True, fontsize=9, sublabel="analyst → tools → grade → report")
    box(ax, 37.5, 37.5, 27, 10.5, "FinScope router", edge=VIOLET, fill=VIOLET_FILL,
        bold=True, fontsize=9, sublabel="classify → 1 of 5 subagents")
    box(ax, 68.5, 37.5, 27, 10.5, "Guardrails", edge=ROSE, fill=ROSE_FILL,
        bold=True, fontsize=9, sublabel="pattern filter, pre-model")

    # Service layer
    band(ax, 3, 14, 94, 17, "SERVICE LAYER   ·   src/finagent/services")
    services = [
        ("documents", 4.5, TEAL), ("vectorstore", 17.8, TEAL), ("mca", 31.1, AMBER),
        ("market_data", 44.4, AMBER), ("search", 57.7, AMBER),
        ("charts", 71.0, INDIGO), ("report", 84.3, INDIGO),
    ]
    for label, x, colour in services:
        fill = {TEAL: TEAL_FILL, AMBER: AMBER_FILL, INDIGO: INDIGO_FILL}[colour]
        box(ax, x, 16.5, 11.5, 7, label, edge=colour, fill=fill, fontsize=7.4)

    # External
    band(ax, 3, 0.5, 94, 11, "EXTERNAL")
    externals = [("Groq LLM", 5), ("Qdrant", 20.5), ("HuggingFace\nencoder", 36),
                 ("MCA registry", 51.5), ("RapidAPI", 67), ("DuckDuckGo", 82.5)]
    for label, x in externals:
        box(ax, x, 2, 13.5, 6, label, edge=MUTED, fill="#ffffff", fontsize=7.2)

    for x in (19.5, 49.5, 79.5):
        arrow(ax, (x, 77.3), (x, 65.3))
    for x in (20, 51, 82):
        arrow(ax, (x, 58.3), (x, 48.2))
    for x in (20, 51, 82):
        arrow(ax, (x, 37.3), (x, 23.7))
    for x in (23.5, 50, 63.5, 90):
        arrow(ax, (x, 16.3), (x, 8.2), dashed=True)

    return save(fig, "architecture.png")


# ─── 2. Evaluation graph ──────────────────────────────────────────────────────

def draw_evaluation_graph() -> Path:
    fig, ax = new_figure(10, 7.2)
    title(ax, "Startup Evaluation Workflow (LangGraph)",
          "The retrieve–grade–rewrite loop is what stops a thin search "
          "becoming an invented thesis")

    circle(ax, 7, 77, 4.2, "START")
    box(ax, 20, 71, 26, 12, "analyst", edge=INDIGO, fill=INDIGO_FILL, bold=True,
        fontsize=9.5, sublabel="assembles profile + docs\n+ registry, binds tools")
    diamond(ax, 64, 77, 20, 13, "tools\nneeded?")
    box(ax, 20, 47, 26, 11, "tools", edge=TEAL, fill=TEAL_FILL, bold=True,
        fontsize=9.5, sublabel="web search\n(failures become messages)")
    diamond(ax, 64, 52.5, 22, 14, "evidence\nsufficient?")
    box(ax, 6, 22, 27, 11, "rewrite", edge=AMBER, fill=AMBER_FILL, bold=True,
        fontsize=9.5, sublabel="narrow the query\n(max 2 attempts)")
    box(ax, 57, 22, 30, 11, "generate", edge=VIOLET, fill=VIOLET_FILL, bold=True,
        fontsize=9.5, sublabel="write the 11-section\nMarkdown report")
    circle(ax, 91, 11, 4.2, "END")

    arrow(ax, (11.2, 77), (19.5, 77))
    arrow(ax, (46, 77), (54.5, 77))

    # tools needed? → yes: down-left into the tools node
    arrow(ax, (64, 70.5), (36, 58.5), label="yes", label_offset=(6, 3), curve=0.12)
    # tools needed? → no: straight to generate, sweeping down the right edge
    arrow(ax, (74, 77), (85, 33.2), label="no", label_offset=(11, 18), curve=-0.32)

    arrow(ax, (46, 52.5), (53.2, 52.5))
    arrow(ax, (64, 45.5), (69, 33.2), label="yes", label_offset=(4.5, 1))
    # evidence? → no: back to rewrite
    arrow(ax, (53.2, 52.5), (26, 33.2), label="no", label_offset=(-4, -3), curve=0.18)
    # rewrite → analyst (not tools): the loop re-runs the analyst
    arrow(ax, (12, 33), (24, 70.8), label="re-run analyst", label_offset=(-7, 2), curve=-0.22)
    arrow(ax, (85, 22), (91, 15.5))

    ax.text(44, 5, "Bounded loop: at most 2 rewrites, recursion limit 15. An "
                   "unsearchable company still\ngets a report — one that says so.",
            ha="center", fontsize=7.6, color=MUTED, style="italic", family=FONT,
            linespacing=1.6)
    return save(fig, "evaluation_graph.png")


# ─── 3. FinScope router ───────────────────────────────────────────────────────

def draw_finscope_router() -> Path:
    fig, ax = new_figure(11, 6.6)
    title(ax, "FinScope — Intent Router",
          "One classifier, five specialists; keyword fast-paths skip the model entirely")

    circle(ax, 8, 62, 4, "START")
    box(ax, 17, 72, 26, 8.5, "guardrail filter", edge=ROSE, fill=ROSE_FILL,
        bold=True, fontsize=8.5, sublabel="deterministic, pre-model")
    box(ax, 18, 55, 24, 11, "classify_intent", edge=INDIGO, fill=INDIGO_FILL,
        bold=True, fontsize=9, sublabel="keyword fast-path,\nthen LLM fallback")

    subagents = [
        ("Financial\nEducator", "education", 3.0, TEAL, TEAL_FILL, "+ YouTube search"),
        ("Document\nAnalyzer", "document", 21.8, VIOLET, VIOLET_FILL, "→ [FLASHCARD]"),
        ("Market\nResearcher", "market", 40.6, INDIGO, INDIGO_FILL, "sector trends"),
        ("Portfolio\nCoach", "strategy", 59.4, AMBER, AMBER_FILL, "→ [PORTFOLIO_FORM]"),
        ("News\nReporter", "news", 78.2, ROSE, ROSE_FILL, "+ live RapidAPI"),
    ]
    for label, intent, x, edge, fill, note in subagents:
        box(ax, x, 22, 17.5, 14, label, edge=edge, fill=fill, bold=True,
            fontsize=8.4, sublabel=note)
        arrow(ax, (30, 54.8), (x + 8.75, 36.5), label=intent,
              label_offset=(0, 1.2), curve=0.05, fontsize=6.8)
        arrow(ax, (x + 8.75, 22), (x + 8.75, 13.5))

    band(ax, 2, 8, 94, 5.5, "", color=LINE, fill=SLATE_FILL)
    ax.text(50, 10.6, "END   ·   the answer carries the agent that produced it "
                      "(agent_used, intent)",
            ha="center", va="center", fontsize=8, color=MUTED, family=FONT)

    arrow(ax, (12, 63.5), (16.5, 74))
    arrow(ax, (30, 72), (30, 66.2))
    ax.text(46, 76, "blocked → HTTP 400, no model call", fontsize=7.2,
            color=ROSE, family=FONT, va="center")
    return save(fig, "finscope_router.png")


# ─── 4. RAG pipeline ──────────────────────────────────────────────────────────

def draw_rag_pipeline() -> Path:
    fig, ax = new_figure(11, 6.2)
    title(ax, "Document Ingestion and Retrieval",
          "Three extractors, one fallback path — a missing vector store never "
          "blocks an evaluation")

    band(ax, 3, 44, 94, 34, "INGEST   (POST /startups/{id}/documents)")
    box(ax, 6, 60, 17, 9, "PDF / DOCX", edge=MUTED, fill="#ffffff", fontsize=8)
    box(ax, 27, 60, 17, 9, "Docling", edge=TEAL, fill=TEAL_FILL, fontsize=8,
        sublabel="tables, headings")
    box(ax, 27, 48, 17, 9, "PyPDF2 →\npdfplumber", edge=TEAL, fill=TEAL_FILL,
        fontsize=7.6, sublabel="fallback chain")
    box(ax, 49, 54.5, 18, 10, "chunk", edge=INDIGO, fill=INDIGO_FILL, fontsize=8.5,
        bold=True, sublabel="1000 chars\n200 overlap")
    box(ax, 72, 54.5, 21, 10, "embed + upsert", edge=INDIGO, fill=INDIGO_FILL,
        fontsize=8.5, bold=True, sublabel="MiniLM-L6-v2 · 384-d")

    arrow(ax, (23, 64.5), (26.5, 64.5))
    arrow(ax, (23, 63), (26.5, 53), dashed=True, label="if empty",
          label_offset=(-1.5, -2.6), fontsize=6.6)
    arrow(ax, (44, 64.5), (48.5, 60.5))
    arrow(ax, (44, 52.5), (48.5, 57))
    arrow(ax, (67, 59.5), (71.5, 59.5))

    box(ax, 72, 33, 21, 8, "Qdrant collection", edge=MUTED, fill="#ffffff",
        fontsize=8, sublabel="startup_<id>  ·  cosine")
    box(ax, 44, 33, 22, 8, "extracted_text", edge=AMBER, fill=AMBER_FILL,
        fontsize=8, sublabel="in-memory fallback")
    arrow(ax, (82.5, 54), (82.5, 41.5))
    arrow(ax, (55, 54), (55, 41.5), dashed=True)

    band(ax, 3, 3, 94, 26, "RETRIEVE   (during analysis and investor chat)")
    box(ax, 6, 12, 19, 9, "query", edge=MUTED, fill="#ffffff", fontsize=8.5)
    box(ax, 30, 12, 21, 9, "top-k search", edge=INDIGO, fill=INDIGO_FILL,
        fontsize=8.5, bold=True, sublabel="k = 6")
    box(ax, 56, 12, 19, 9, "context block", edge=INDIGO, fill=INDIGO_FILL, fontsize=8.5)
    box(ax, 79, 12, 15, 9, "agent prompt", edge=VIOLET, fill=VIOLET_FILL,
        fontsize=8.5, bold=True)

    arrow(ax, (25, 16.5), (29.5, 16.5))
    arrow(ax, (51, 16.5), (55.5, 16.5))
    arrow(ax, (75, 16.5), (78.5, 16.5))
    arrow(ax, (82.5, 33), (45, 20.5), curve=-0.18, dashed=True)
    # The in-memory text substitutes for the retrieved context when search is empty.
    arrow(ax, (55, 33), (63, 21.5), curve=-0.2, dashed=True, label="if no hits",
          label_offset=(-7, 1), fontsize=6.6, color=AMBER, label_color=AMBER)
    return save(fig, "rag_pipeline.png")


# ─── 5. Request sequence ──────────────────────────────────────────────────────

def draw_sequence() -> Path:
    fig, ax = new_figure(10, 7)
    title(ax, "Report Generation — Request Sequence",
          "POST /reports/{id} from call to PDF")

    lanes: Sequence[Tuple[str, float, str]] = [
        ("Client", 8, MUTED),
        ("API", 27, INDIGO),
        ("Graph", 46, VIOLET),
        ("Services", 65, TEAL),
        ("External", 87, AMBER),
    ]
    for label, x, colour in lanes:
        box(ax, x - 8, 84, 16, 6.5, label, edge=colour,
            fill={MUTED: "#ffffff", INDIGO: INDIGO_FILL, VIOLET: VIOLET_FILL,
                  TEAL: TEAL_FILL, AMBER: AMBER_FILL}[colour],
            bold=True, fontsize=8.5)
        ax.plot([x, x], [8, 84], color=LINE, linewidth=0.9, linestyle=":", zorder=0)

    steps: Iterable[Tuple[float, float, float, str, bool]] = [
        (78, 8, 27, "POST /reports/{id}", False),
        (72.5, 27, 46, "run(startup)", False),
        (67, 46, 65, "retrieve documents", False),
        (61.5, 65, 87, "Qdrant search", False),
        (56, 87, 65, "chunks", True),
        (50.5, 46, 87, "LLM: analyse + tool call", False),
        (45, 87, 46, "web results", True),
        (39, 46, 46, "grade evidence", False),
        (32, 46, 87, "LLM: write report", False),
        (26.5, 87, 46, "Markdown", True),
        (21, 46, 27, "analysis text", True),
        (15.5, 27, 65, "build_pdf()", False),
        (10, 65, 65, "render 3 charts", False),
        (4.5, 27, 8, "application/pdf", True),
    ]
    for y, x0, x1, label, is_return in steps:
        if x0 == x1:
            ax.annotate("", xy=(x0 + 6, y - 1.2), xytext=(x0, y + 1.0),
                        arrowprops=dict(arrowstyle="-|>", color=LINE, linewidth=1.1,
                                        connectionstyle="arc3,rad=-1.6"))
            ax.text(x0 + 8.5, y + 0.2, label, fontsize=7, color=MUTED,
                    va="center", family=FONT)
            continue
        arrow(ax, (x0, y), (x1, y), dashed=is_return,
              color=LINE if not is_return else "#cbd5e1")
        ax.text((x0 + x1) / 2, y + 1.9, label, ha="center", fontsize=7,
                color=MUTED if not is_return else "#94a3b8", family=FONT,
                style="italic" if is_return else "normal",
                bbox=dict(boxstyle="round,pad=0.2", facecolor=BG, edgecolor="none"))

    ax.text(50, 0.5, "Every log line on this path is mirrored to Socket.IO "
                     "(channel: log_stream) so the client can show progress.",
            ha="center", fontsize=7.4, color=MUTED, style="italic", family=FONT)
    return save(fig, "request_sequence.png")


# ─── 6. Deployment ────────────────────────────────────────────────────────────

def draw_deployment() -> Path:
    fig, ax = new_figure(10, 6)
    title(ax, "Deployment Topology", "One container, one port; every dependency optional")

    band(ax, 3, 42, 55, 44, "DOCKER HOST  /  docker compose")
    box(ax, 7, 62, 46, 18, "finagent", edge=INDIGO, fill=INDIGO_FILL, bold=True,
        fontsize=10, sublabel="python:3.11-slim  ·  uvicorn  ·  non-root uid 1000\n"
                              "REST + Socket.IO on :7860  ·  /health")
    box(ax, 7, 46, 20, 9, "qdrant", edge=TEAL, fill=TEAL_FILL, bold=True,
        fontsize=9, sublabel=":6333  ·  volume")
    box(ax, 33, 46, 20, 9, ".env", edge=MUTED, fill="#ffffff", fontsize=9,
        sublabel="secrets, never in git")
    arrow(ax, (17, 62), (17, 55.5), label="vectors", label_offset=(-7, 0), fontsize=6.8)
    arrow(ax, (43, 62), (43, 55.5), label="config", label_offset=(6.5, 0), fontsize=6.8)

    band(ax, 62, 42, 35, 44, "MANAGED SERVICES")
    for label, y, note in [
        ("Groq", 72, "LLM inference — required"),
        ("RapidAPI", 63, "live news — optional"),
        ("MCA provider", 54, "registry — optional"),
        ("DuckDuckGo", 45, "web search — optional"),
    ]:
        box(ax, 65, y, 29, 7.5, label, edge=AMBER, fill=AMBER_FILL, fontsize=8,
            sublabel=note)
        arrow(ax, (53, 70), (64.5, y + 3.7), curve=0.08, dashed=True)

    box(ax, 18, 24, 26, 8, "Client / browser", edge=MUTED, fill="#ffffff", fontsize=8.5)
    # Label sits in the empty band between the client box and the service row.
    arrow(ax, (31, 32), (30, 61.5), label="HTTP + WebSocket",
          label_offset=(0, -7.5), fontsize=7)

    ax.text(50, 15, "Degradation is the design: no Qdrant → in-memory document text; "
                    "no registry key → sandbox provider;\nno RapidAPI key → the News "
                    "Reporter works from model knowledge. Only GROQ_API_KEY is required.",
            ha="center", fontsize=7.6, color=MUTED, family=FONT, linespacing=1.6)
    return save(fig, "deployment.png")


# ─── 7. Module map ────────────────────────────────────────────────────────────

def draw_module_map() -> Path:
    fig, ax = new_figure(10, 6.4)
    title(ax, "Package Layout", "src/finagent — dependencies point downward only")

    groups = [
        ("api/", 5, 80, ["routes/startups.py", "routes/documents.py", "routes/reports.py",
                         "routes/verification.py", "routes/chat.py", "routes/finscope.py",
                         "routes/health.py", "deps.py"], INDIGO, INDIGO_FILL),
        ("agents/", 37.5, 80, ["evaluation_graph.py", "finscope_graph.py",
                               "prompts.py", "tools.py", "guardrails.py"], VIOLET, VIOLET_FILL),
        ("services/", 69, 80, ["documents.py", "vectorstore.py", "mca.py",
                               "market_data.py", "search.py", "charts.py",
                               "report.py", "runtime.py", "startups.py"], TEAL, TEAL_FILL),
    ]
    for name, x, y, files, edge, fill in groups:
        height = 8 + len(files) * 4.4
        box(ax, x, y - height + 6, 26, height, "", edge=edge, fill=fill)
        ax.text(x + 13, y + 2.2, name, ha="center", fontsize=9.5, color=INK,
                fontweight="bold", family=FONT)
        for index, filename in enumerate(files):
            ax.text(x + 13, y - 2.4 - index * 4.4, filename, ha="center",
                    fontsize=7.2, color=MUTED, family=FONT)

    for label, x in [("app.py", 5), ("schemas.py", 26), ("settings.py", 47),
                     ("store.py", 68), ("realtime.py", 85)]:
        box(ax, x, 13, 14 if x < 80 else 13, 7.5, label, edge=MUTED, fill="#ffffff",
            fontsize=8)

    ax.text(50, 6, "app.py wires the routers · schemas.py is the wire contract · "
                   "settings.py is the only reader of os.environ",
            ha="center", fontsize=7.5, color=MUTED, style="italic", family=FONT)

    arrow(ax, (31, 55), (37, 55), color=LINE)
    arrow(ax, (63.5, 55), (69, 55), color=LINE)
    ax.text(34, 58, "uses", fontsize=6.8, color=MUTED, ha="center", family=FONT)
    ax.text(66, 58, "uses", fontsize=6.8, color=MUTED, ha="center", family=FONT)
    return save(fig, "module_map.png")


DIAGRAMS = [
    draw_architecture,
    draw_evaluation_graph,
    draw_finscope_router,
    draw_rag_pipeline,
    draw_sequence,
    draw_deployment,
    draw_module_map,
]


def main() -> None:
    print("Rendering diagrams...")
    for render in DIAGRAMS:
        render()
    print(f"Done — {len(DIAGRAMS)} diagrams in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
