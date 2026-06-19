"""Deterministic, local PDF rendering for validated document plans."""

from __future__ import annotations

from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .schemas import DocumentPlan

INK = colors.HexColor("#172033")
MUTED = colors.HexColor("#667085")
ACCENT = colors.HexColor("#2F6DF6")
PALE_ACCENT = colors.HexColor("#EDF3FF")
RULE = colors.HexColor("#DCE2EC")
PAPER = colors.HexColor("#FFFFFF")


def _markup(text: str) -> str:
    """Escape provider output before ReportLab interprets its small markup language."""
    return escape(text).replace("\n", "<br/>")


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TypesetTitle",
            parent=base["Title"],
            fontName="Times-Bold",
            fontSize=31,
            leading=35,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=5 * mm,
        ),
        "subtitle": ParagraphStyle(
            "TypesetSubtitle",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=12,
            leading=18,
            textColor=MUTED,
            spaceAfter=8 * mm,
        ),
        "summary": ParagraphStyle(
            "TypesetSummary",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=11,
            leading=17,
            textColor=INK,
        ),
        "heading": ParagraphStyle(
            "TypesetHeading",
            parent=base["Heading2"],
            fontName="Times-Bold",
            fontSize=19,
            leading=23,
            textColor=INK,
            spaceBefore=8 * mm,
            spaceAfter=3.5 * mm,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "TypesetBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=16.5,
            textColor=INK,
            spaceAfter=3.5 * mm,
            allowWidows=0,
            allowOrphans=0,
        ),
        "callout": ParagraphStyle(
            "TypesetCallout",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=15,
            textColor=INK,
        ),
    }


def _draw_page(canvas, document) -> None:
    """Apply consistent publication furniture after body flow has been calculated."""
    width, height = A4
    canvas.saveState()
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, width, height, stroke=0, fill=1)

    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(1.6)
    canvas.line(22 * mm, height - 17 * mm, 38 * mm, height - 17 * mm)

    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.drawString(22 * mm, height - 13 * mm, "TYPESET")

    page_label = str(document.page)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(width - 22 * mm, 13 * mm, page_label)
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(22 * mm, 17 * mm, width - 22 * mm, 17 * mm)
    canvas.restoreState()


def _summary_block(text: str, style: ParagraphStyle, content_width: float) -> Table:
    summary = Table(
        [[Paragraph(_markup(text), style)]],
        colWidths=[content_width],
        hAlign="LEFT",
    )
    summary.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE_ACCENT),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#C8D8FF")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5 * mm),
            ]
        )
    )
    return summary


def _callout_block(text: str, style: ParagraphStyle, content_width: float) -> Table:
    callout = Table(
        [["", Paragraph(_markup(text), style)]],
        colWidths=[2.5 * mm, content_width - 2.5 * mm],
        hAlign="LEFT",
    )
    callout.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), ACCENT),
                ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#F7F9FC")),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
                ("RIGHTPADDING", (0, 0), (0, -1), 0),
                ("LEFTPADDING", (1, 0), (1, -1), 5 * mm),
                ("RIGHTPADDING", (1, 0), (1, -1), 5 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
            ]
        )
    )
    return callout


def render_document(plan: DocumentPlan) -> bytes:
    """Render a polished A4 PDF entirely in memory."""
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=22 * mm,
        leftMargin=22 * mm,
        topMargin=27 * mm,
        bottomMargin=23 * mm,
        title=plan.title,
        author="Typeset",
        subject="AI-assisted document layout",
    )
    styles = _styles()
    story = [Spacer(1, 8 * mm), Paragraph(_markup(plan.title), styles["title"])]

    if plan.subtitle:
        story.append(Paragraph(_markup(plan.subtitle), styles["subtitle"]))
    else:
        story.append(Spacer(1, 3 * mm))

    if plan.summary:
        story.extend(
            [
                _summary_block(plan.summary, styles["summary"], document.width),
                Spacer(1, 5 * mm),
            ]
        )

    for section in plan.sections:
        first_paragraph = Paragraph(_markup(section.paragraphs[0]), styles["body"])
        story.append(
            KeepTogether(
                [Paragraph(_markup(section.heading), styles["heading"]), first_paragraph]
            )
        )
        story.extend(
            Paragraph(_markup(paragraph), styles["body"])
            for paragraph in section.paragraphs[1:]
        )
        if section.callout:
            story.extend(
                [
                    Spacer(1, 2 * mm),
                    _callout_block(section.callout, styles["callout"], document.width),
                    Spacer(1, 2 * mm),
                ]
            )

    document.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    return buffer.getvalue()
