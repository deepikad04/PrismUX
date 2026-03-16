"""Generate polished PDF friction reports using ReportLab."""

from __future__ import annotations

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from schemas.report import FrictionReport

# Brand colors
PRIMARY = colors.HexColor("#4f46e5")
PRIMARY_LIGHT = colors.HexColor("#e0e7ff")
SURFACE_700 = colors.HexColor("#374151")
SURFACE_500 = colors.HexColor("#6b7280")
SURFACE_200 = colors.HexColor("#e5e7eb")

SEVERITY_COLORS = {
    "critical": colors.HexColor("#dc2626"),
    "high": colors.HexColor("#ef4444"),
    "medium": colors.HexColor("#f59e0b"),
    "low": colors.HexColor("#3b82f6"),
}

SEVERITY_BG = {
    "critical": colors.HexColor("#fef2f2"),
    "high": colors.HexColor("#fef2f2"),
    "medium": colors.HexColor("#fffbeb"),
    "low": colors.HexColor("#eff6ff"),
}


def _get_styles():
    """Build custom paragraph styles."""
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "PDFTitle",
            parent=base["Title"],
            fontSize=28,
            textColor=PRIMARY,
            spaceAfter=6 * mm,
        ),
        "subtitle": ParagraphStyle(
            "PDFSubtitle",
            parent=base["Normal"],
            fontSize=11,
            textColor=SURFACE_500,
            spaceAfter=4 * mm,
        ),
        "heading": ParagraphStyle(
            "PDFHeading",
            parent=base["Heading2"],
            fontSize=14,
            textColor=SURFACE_700,
            spaceBefore=8 * mm,
            spaceAfter=4 * mm,
        ),
        "body": ParagraphStyle(
            "PDFBody",
            parent=base["Normal"],
            fontSize=10,
            textColor=SURFACE_700,
            leading=14,
        ),
        "small": ParagraphStyle(
            "PDFSmall",
            parent=base["Normal"],
            fontSize=8,
            textColor=SURFACE_500,
        ),
        "metric_value": ParagraphStyle(
            "MetricValue",
            parent=base["Normal"],
            fontSize=22,
            alignment=TA_CENTER,
            textColor=SURFACE_700,
        ),
        "metric_label": ParagraphStyle(
            "MetricLabel",
            parent=base["Normal"],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=SURFACE_500,
        ),
        "cell": ParagraphStyle(
            "CellText",
            parent=base["Normal"],
            fontSize=8,
            textColor=SURFACE_700,
            leading=10,
        ),
        "cell_bold": ParagraphStyle(
            "CellBold",
            parent=base["Normal"],
            fontSize=8,
            textColor=SURFACE_700,
            leading=10,
            fontName="Helvetica-Bold",
        ),
    }
    return styles


def _score_color(score: float) -> colors.HexColor:
    if score <= 25:
        return colors.HexColor("#16a34a")
    if score <= 50:
        return colors.HexColor("#f59e0b")
    if score <= 75:
        return colors.HexColor("#ef4444")
    return colors.HexColor("#dc2626")


def _build_cover(report: FrictionReport, styles: dict) -> list:
    """Build cover page elements."""
    elements = []

    elements.append(Spacer(1, 3 * cm))
    elements.append(Paragraph("PrismUX", styles["title"]))
    elements.append(Paragraph("UX Friction Report", ParagraphStyle(
        "CoverSub",
        parent=styles["subtitle"],
        fontSize=16,
        textColor=SURFACE_700,
        spaceAfter=12 * mm,
    )))

    # Metadata table
    meta_data = [
        ["URL", report.url],
        ["Goal", report.goal],
        ["Persona", report.persona or "Default"],
        ["Date", datetime.utcnow().strftime("%B %d, %Y")],
        ["Status", report.status.capitalize()],
    ]
    meta_table = Table(meta_data, colWidths=[3 * cm, 12 * cm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), SURFACE_500),
        ("TEXTCOLOR", (1, 0), (1, -1), SURFACE_700),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, SURFACE_200),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(meta_table)

    elements.append(Spacer(1, 15 * mm))

    # Friction score — big number
    score_color = _score_color(report.friction_score)
    elements.append(Paragraph(
        f'<font color="{score_color.hexval()}" size="48"><b>{report.friction_score:.0f}</b></font>',
        ParagraphStyle("ScoreNum", alignment=TA_CENTER, spaceAfter=2 * mm),
    ))
    elements.append(Paragraph(
        "Friction Score (0 = frictionless, 100 = unusable)",
        ParagraphStyle("ScoreLabel", alignment=TA_CENTER, fontSize=9, textColor=SURFACE_500),
    ))

    return elements


def _build_summary(report: FrictionReport, styles: dict) -> list:
    """Build executive summary + metrics section."""
    elements = []

    # Metrics row
    elements.append(Paragraph("Key Metrics", styles["heading"]))
    metrics_data = [[
        Paragraph(f"<b>{report.total_steps}</b>", styles["metric_value"]),
        Paragraph(f"<b>{report.total_time_seconds:.1f}s</b>", styles["metric_value"]),
        Paragraph(f"<b>{len(report.friction_items)}</b>", styles["metric_value"]),
        Paragraph(f"<b>{report.friction_score:.0f}</b>", styles["metric_value"]),
    ], [
        Paragraph("Steps", styles["metric_label"]),
        Paragraph("Duration", styles["metric_label"]),
        Paragraph("Friction Points", styles["metric_label"]),
        Paragraph("Score", styles["metric_label"]),
    ]]
    metrics_table = Table(metrics_data, colWidths=[3.75 * cm] * 4)
    metrics_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, SURFACE_200),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, SURFACE_200),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_LIGHT),
    ]))
    elements.append(metrics_table)

    # Error classification
    if report.error_classification and report.error_classification.error_type != "none":
        elements.append(Paragraph("Error Classification", styles["heading"]))
        ec = report.error_classification
        error_data = [
            [
                Paragraph("<b>Type</b>", styles["cell_bold"]),
                Paragraph("<b>Details</b>", styles["cell_bold"]),
                Paragraph("<b>Recoverable</b>", styles["cell_bold"]),
            ],
            [
                Paragraph(ec.error_type.replace("_", " ").upper(), styles["cell_bold"]),
                Paragraph(ec.details, styles["cell"]),
                Paragraph("Yes" if ec.recoverable else "No", styles["cell"]),
            ],
        ]
        error_table = Table(error_data, colWidths=[3 * cm, 9.5 * cm, 2.5 * cm])
        error_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fef2f2")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#dc2626")),
            ("BOX", (0, 0), (-1, -1), 0.5, SURFACE_200),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, SURFACE_200),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(error_table)

    # Executive summary
    if report.executive_summary:
        elements.append(Paragraph("Executive Summary", styles["heading"]))
        elements.append(Paragraph(report.executive_summary, styles["body"]))

    # Improvement priorities
    if report.improvement_priorities:
        elements.append(Paragraph("Improvement Priorities", styles["heading"]))
        for i, priority in enumerate(report.improvement_priorities, 1):
            elements.append(Paragraph(
                f"<b>{i}.</b> {priority}",
                ParagraphStyle("Priority", parent=styles["body"], spaceAfter=3 * mm),
            ))

    return elements


def _build_friction_table(report: FrictionReport, styles: dict) -> list:
    """Build friction items table."""
    elements = []
    elements.append(Paragraph("Friction Points", styles["heading"]))

    if not report.friction_items:
        elements.append(Paragraph(
            "<i>No friction points detected.</i>", styles["body"],
        ))
        return elements

    # Table header
    header = [
        Paragraph("<b>#</b>", styles["cell_bold"]),
        Paragraph("<b>Category</b>", styles["cell_bold"]),
        Paragraph("<b>Severity</b>", styles["cell_bold"]),
        Paragraph("<b>Description</b>", styles["cell_bold"]),
        Paragraph("<b>Suggestion</b>", styles["cell_bold"]),
        Paragraph("<b>Step</b>", styles["cell_bold"]),
    ]

    rows = [header]
    row_colors = []

    for i, item in enumerate(report.friction_items):
        sev_color = SEVERITY_COLORS.get(item.severity, SURFACE_500)
        row_bg = SEVERITY_BG.get(item.severity, colors.white)
        row_colors.append(row_bg)

        rows.append([
            Paragraph(str(i + 1), styles["cell"]),
            Paragraph(item.category.upper(), styles["cell_bold"]),
            Paragraph(
                f'<font color="{sev_color.hexval()}">{item.severity.upper()}</font>',
                styles["cell_bold"],
            ),
            Paragraph(item.description, styles["cell"]),
            Paragraph(item.improvement_suggestion or "—", styles["cell"]),
            Paragraph(str(item.evidence_step), styles["cell"]),
        ])

    col_widths = [1 * cm, 2.2 * cm, 1.8 * cm, 5.5 * cm, 4.5 * cm, 1 * cm]
    table = Table(rows, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (5, 0), (5, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, SURFACE_200),
        ("BOX", (0, 0), (-1, -1), 0.5, SURFACE_200),
    ]

    # Apply row background colors
    for i, bg in enumerate(row_colors):
        style_cmds.append(("BACKGROUND", (0, i + 1), (-1, i + 1), bg))

    table.setStyle(TableStyle(style_cmds))
    elements.append(table)

    return elements


def _build_timeline(report: FrictionReport, styles: dict) -> list:
    """Build step timeline table."""
    elements = []
    elements.append(Paragraph("Step Timeline", styles["heading"]))

    if not report.step_timeline:
        elements.append(Paragraph("<i>No steps recorded.</i>", styles["body"]))
        return elements

    header = [
        Paragraph("<b>Step</b>", styles["cell_bold"]),
        Paragraph("<b>Action</b>", styles["cell_bold"]),
        Paragraph("<b>Target</b>", styles["cell_bold"]),
        Paragraph("<b>Reasoning</b>", styles["cell_bold"]),
        Paragraph("<b>Friction</b>", styles["cell_bold"]),
        Paragraph("<b>Conf.</b>", styles["cell_bold"]),
    ]

    rows = [header]
    for step in report.step_timeline:
        friction_text = ", ".join(step.friction_detected) if step.friction_detected else "—"
        rows.append([
            Paragraph(str(step.step_number), styles["cell"]),
            Paragraph(step.action_type, styles["cell_bold"]),
            Paragraph(step.target or "—", styles["cell"]),
            Paragraph(step.reasoning, styles["cell"]),
            Paragraph(friction_text, styles["cell"]),
            Paragraph(f"{step.confidence:.2f}", styles["cell"]),
        ])

    col_widths = [1 * cm, 1.8 * cm, 3 * cm, 4.5 * cm, 4.2 * cm, 1.5 * cm]
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (5, 0), (5, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, SURFACE_200),
        ("BOX", (0, 0), (-1, -1), 0.5, SURFACE_200),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
    ]))
    elements.append(table)

    return elements


def _footer(canvas, doc):
    """Draw footer on every page."""
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(SURFACE_500)
    canvas.drawString(2 * cm, 1.2 * cm, f"PrismUX Friction Report — Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


def generate_pdf(report: FrictionReport) -> bytes:
    """Generate a complete PDF friction report and return raw bytes."""
    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title=f"PrismUX Friction Report — {report.session_id}",
        author="PrismUX",
    )

    styles = _get_styles()

    story = []
    story.extend(_build_cover(report, styles))
    story.extend(_build_summary(report, styles))
    story.extend(_build_friction_table(report, styles))
    story.extend(_build_timeline(report, styles))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)

    return buf.getvalue()
