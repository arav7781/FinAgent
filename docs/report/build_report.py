#!/usr/bin/env python3
"""Render the FinAgent project report to PDF.

Content lives in `content.py`; this module is the renderer — styles, flowables,
figure captions, page furniture. Regenerates the diagrams first so the report
can never ship a stale figure.

    python docs/report/build_report.py
    make report
"""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image as RLImage,
    KeepTogether,
    ListFlowable,
    ListItem,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

from content import (  # noqa: E402
    AUTHOR,
    COVER_BLURB,
    DOC_DATE,
    REPO_URL,
    SECTIONS,
    SUBTITLE,
    TITLE,
)

DIAGRAM_DIR = REPO_ROOT / "docs" / "diagrams"
OUTPUT_PATH = REPO_ROOT / "report" / "FinAgent_Report.pdf"

# ─── Palette ──────────────────────────────────────────────────────────────────

INK = colors.HexColor("#0f172a")
BODY = colors.HexColor("#1e293b")
MUTED = colors.HexColor("#64748b")
ACCENT = colors.HexColor("#4f46e5")
ACCENT_SOFT = colors.HexColor("#eef2ff")
BORDER = colors.HexColor("#e2e8f0")
SURFACE = colors.HexColor("#f8fafc")
CODE_BG = colors.HexColor("#f1f5f9")

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 2.2 * cm
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN


# ─── Styles ───────────────────────────────────────────────────────────────────

def build_styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "CoverTitle", parent=base["Title"], fontSize=34, leading=40,
            textColor=ACCENT, fontName="Helvetica-Bold", alignment=TA_CENTER,
            spaceAfter=4),
        "cover_sub": ParagraphStyle(
            "CoverSub", parent=base["Normal"], fontSize=13.5, leading=19,
            textColor=BODY, alignment=TA_CENTER, spaceAfter=18),
        "cover_meta": ParagraphStyle(
            "CoverMeta", parent=base["Normal"], fontSize=10, leading=16,
            textColor=MUTED, alignment=TA_CENTER),
        "cover_blurb": ParagraphStyle(
            "CoverBlurb", parent=base["Normal"], fontSize=10.5, leading=17,
            textColor=BODY, alignment=TA_JUSTIFY),
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontSize=18, leading=23,
            textColor=ACCENT, fontName="Helvetica-Bold",
            spaceBefore=2, spaceAfter=10),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontSize=12.5, leading=16,
            textColor=INK, fontName="Helvetica-Bold",
            spaceBefore=14, spaceAfter=6),
        "h3": ParagraphStyle(
            "H3", parent=base["Heading3"], fontSize=10.5, leading=14,
            textColor=BODY, fontName="Helvetica-BoldOblique",
            spaceBefore=10, spaceAfter=4),
        "body": ParagraphStyle(
            "Body", parent=base["Normal"], fontSize=9.8, leading=15.2,
            textColor=BODY, alignment=TA_JUSTIFY, spaceAfter=7),
        "bullet": ParagraphStyle(
            "Bullet", parent=base["Normal"], fontSize=9.6, leading=14.4,
            textColor=BODY, alignment=TA_JUSTIFY),
        "caption": ParagraphStyle(
            "Caption", parent=base["Normal"], fontSize=8.4, leading=12,
            textColor=MUTED, alignment=TA_CENTER, spaceBefore=5, spaceAfter=12),
        "code": ParagraphStyle(
            "Code", parent=base["Normal"], fontName="Courier", fontSize=8,
            leading=11.4, textColor=INK, backColor=CODE_BG,
            borderPadding=7, spaceBefore=4, spaceAfter=9, leftIndent=2),
        "callout": ParagraphStyle(
            "Callout", parent=base["Normal"], fontSize=9.6, leading=14.6,
            textColor=BODY, alignment=TA_JUSTIFY, backColor=ACCENT_SOFT,
            borderPadding=9, borderColor=ACCENT, borderWidth=0,
            leftIndent=4, rightIndent=4, spaceBefore=5, spaceAfter=10),
        "table_cell": ParagraphStyle(
            "TableCell", parent=base["Normal"], fontSize=8.6, leading=12.2,
            textColor=BODY),
        "table_head": ParagraphStyle(
            "TableHead", parent=base["Normal"], fontSize=8.6, leading=12.2,
            textColor=colors.white, fontName="Helvetica-Bold"),
        "toc_entry": ParagraphStyle(
            "TocEntry", parent=base["Normal"], fontSize=10.2, leading=20,
            textColor=BODY),
    }


# ─── Page furniture ───────────────────────────────────────────────────────────

def draw_cover_page(canvas, _doc) -> None:
    canvas.saveState()
    canvas.setFillColor(ACCENT)
    canvas.rect(0, PAGE_HEIGHT - 1.0 * cm, PAGE_WIDTH, 1.0 * cm, stroke=0, fill=1)
    canvas.setFillColor(BORDER)
    canvas.rect(0, 0, PAGE_WIDTH, 0.35 * cm, stroke=0, fill=1)
    canvas.restoreState()


def draw_body_page(canvas, doc) -> None:
    canvas.saveState()
    # Header rule and running title
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.6)
    canvas.line(MARGIN, PAGE_HEIGHT - MARGIN + 0.45 * cm,
                PAGE_WIDTH - MARGIN, PAGE_HEIGHT - MARGIN + 0.45 * cm)
    canvas.setFont("Helvetica", 7.6)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, PAGE_HEIGHT - MARGIN + 0.72 * cm,
                      "FinAgent — Project Report")
    canvas.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - MARGIN + 0.72 * cm,
                           AUTHOR)
    # Footer
    canvas.line(MARGIN, MARGIN - 0.55 * cm, PAGE_WIDTH - MARGIN, MARGIN - 0.55 * cm)
    canvas.setFont("Helvetica", 7.6)
    canvas.drawString(MARGIN, MARGIN - 1.0 * cm, REPO_URL)
    canvas.drawRightString(PAGE_WIDTH - MARGIN, MARGIN - 1.0 * cm,
                           f"Page {doc.page - 1}")
    canvas.restoreState()


# ─── Flowable builders ────────────────────────────────────────────────────────

def figure(name: str, caption: str, styles: dict, width_cm: float = 15.6) -> list:
    """An embedded diagram with a numbered caption, kept on one page."""
    path = DIAGRAM_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing diagram: {path}. Run generate_diagrams.py.")

    from PIL import Image as PILImage

    with PILImage.open(path) as image:
        aspect = image.height / image.width

    width = width_cm * cm
    height = width * aspect
    max_height = 17.5 * cm
    if height > max_height:
        height = max_height
        width = height / aspect

    return [KeepTogether([
        RLImage(str(path), width=width, height=height),
        Paragraph(caption, styles["caption"]),
    ])]


def table(rows: list, styles: dict, widths: list | None = None,
          header: bool = True) -> Table:
    """A styled table; the first row is the header unless told otherwise."""
    data = []
    for index, row in enumerate(rows):
        style = styles["table_head"] if (header and index == 0) else styles["table_cell"]
        data.append([Paragraph(str(cell), style) for cell in row])

    if widths is None:
        widths = [CONTENT_WIDTH / len(rows[0])] * len(rows[0])
    else:
        total = sum(widths)
        widths = [w / total * CONTENT_WIDTH for w in widths]

    flowable = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    if header:
        commands += [
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SURFACE]),
        ]
    else:
        commands.append(("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, SURFACE]))
    flowable.setStyle(TableStyle(commands))
    return flowable


def bullets(items: list, styles: dict) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(item, styles["bullet"]), leftIndent=14, value="bullet")
         for item in items],
        bulletType="bullet", bulletFontSize=6, bulletOffsetY=1,
        leftIndent=12, spaceBefore=2, spaceAfter=9,
    )


def render_block(block: tuple, styles: dict, counters: dict) -> list:
    """Turn one content block into flowables."""
    kind, payload = block[0], block[1:]

    if kind == "h2":
        return [Paragraph(payload[0], styles["h2"])]
    if kind == "h3":
        return [Paragraph(payload[0], styles["h3"])]
    if kind == "p":
        return [Paragraph(payload[0], styles["body"])]
    if kind == "bullets":
        return [bullets(payload[0], styles)]
    if kind == "code":
        escaped = (payload[0].replace("&", "&amp;")
                             .replace("<", "&lt;")
                             .replace(">", "&gt;")
                             .replace(" ", "&nbsp;")
                             .replace("\n", "<br/>"))
        return [Paragraph(escaped, styles["code"])]
    if kind == "callout":
        return [Paragraph(payload[0], styles["callout"])]
    if kind == "table":
        rows, widths = payload[0], (payload[1] if len(payload) > 1 else None)
        return [table(rows, styles, widths), Spacer(1, 9)]
    if kind == "figure":
        counters["figure"] += 1
        name, caption = payload[0], payload[1]
        width = payload[2] if len(payload) > 2 else 15.6
        return figure(name, f"<b>Figure {counters['figure']}.</b> {caption}",
                      styles, width)
    if kind == "spacer":
        return [Spacer(1, payload[0])]
    if kind == "pagebreak":
        return [PageBreak()]
    raise ValueError(f"Unknown block type: {kind}")


# ─── Document ─────────────────────────────────────────────────────────────────

def build_cover(styles: dict) -> list:
    return [
        Spacer(1, 3.4 * cm),
        Paragraph(TITLE, styles["cover_title"]),
        Spacer(1, 0.25 * cm),
        Paragraph(SUBTITLE, styles["cover_sub"]),
        HRFlowable(width="42%", thickness=2, color=ACCENT, spaceAfter=22,
                   hAlign="CENTER"),
        Spacer(1, 0.5 * cm),
        Paragraph(COVER_BLURB, styles["cover_blurb"]),
        Spacer(1, 2.6 * cm),
        Paragraph(f"<b>{AUTHOR}</b>", styles["cover_meta"]),
        Paragraph(DOC_DATE, styles["cover_meta"]),
        Spacer(1, 0.5 * cm),
        Paragraph(f'<link href="{REPO_URL}" color="#4f46e5">{REPO_URL}</link>',
                  styles["cover_meta"]),
        NextPageTemplate("body"),
        PageBreak(),
    ]


def build_toc(styles: dict) -> list:
    story = [Paragraph("Contents", styles["h1"]),
             HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=14)]
    rows = []
    for index, section in enumerate(SECTIONS, start=1):
        rows.append([f"<b>{index}.</b>&nbsp;&nbsp;<b>{section['title']}</b>",
                     section["summary"]])
    story.append(table(rows, styles, widths=[34, 66], header=False))
    story.append(Spacer(1, 14))
    story.append(Paragraph(
        "Diagrams in this report are rendered from "
        "<font face='Courier' size='8'>docs/diagrams/generate_diagrams.py</font> "
        "and the document itself is rebuilt with "
        "<font face='Courier' size='8'>make report</font>, so no figure can drift "
        "from the code it describes.",
        styles["body"]))
    story.append(PageBreak())
    return story


def build_story(styles: dict) -> list:
    counters = {"figure": 0}
    story = build_cover(styles) + build_toc(styles)

    for index, section in enumerate(SECTIONS, start=1):
        story.append(Paragraph(f"{index}.&nbsp;&nbsp;{section['title']}", styles["h1"]))
        story.append(HRFlowable(width="100%", thickness=1.4, color=ACCENT,
                                spaceAfter=12))
        for block in section["blocks"]:
            story.extend(render_block(block, styles, counters))
        if index < len(SECTIONS):
            story.append(PageBreak())

    return story


def main() -> None:
    print("Regenerating diagrams...")
    sys.path.insert(0, str(DIAGRAM_DIR))
    import generate_diagrams

    generate_diagrams.main()

    print("Building the report...")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    styles = build_styles()

    doc = BaseDocTemplate(
        str(OUTPUT_PATH), pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title=TITLE, author=AUTHOR,
        subject="FinTech application report — AI in banking and finance",
    )
    frame = Frame(MARGIN, MARGIN, CONTENT_WIDTH,
                  PAGE_HEIGHT - 2 * MARGIN, id="main")
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[frame], onPage=draw_cover_page),
        PageTemplate(id="body", frames=[frame], onPage=draw_body_page),
    ])

    doc.build(build_story(styles))
    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)} ({size_kb:,.0f} KB, "
          f"{doc.page} pages)")


if __name__ == "__main__":
    main()
