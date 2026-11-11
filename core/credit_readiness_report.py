"""Generate a factual, printable MSME credit-readiness report."""

from datetime import date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether,
)


def build_credit_readiness_pdf(business_name, result):
    """Return a PDF containing only supplied assessment data and explanations."""
    if not isinstance(business_name, str) or not business_name.strip():
        raise ValueError("A business name is required.")
    required = {
        "status", "latest_month", "months_reviewed", "latest_cash_headroom",
        "average_three_month_headroom", "positive_headroom_months",
        "proposed_monthly_emi", "headroom_after_proposed_emi",
        "coverage_proxy", "revenue_change_percent", "findings",
        "evidence_gaps", "limitations",
    }
    missing = required.difference(result)
    if missing:
        raise ValueError("Assessment result is missing required report fields.")

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title="MSME Credit Readiness Review",
        author="MSME Financial Platform",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=20, leading=25, textColor=colors.HexColor("#172554"),
        alignment=TA_LEFT, spaceAfter=5 * mm,
    ))
    styles.add(ParagraphStyle(
        name="Section", parent=styles["Heading2"], fontSize=12,
        leading=15, textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=5 * mm, spaceAfter=2 * mm,
    ))
    styles.add(ParagraphStyle(
        name="SmallNote", parent=styles["BodyText"], fontSize=8,
        leading=11, textColor=colors.HexColor("#475569"),
    ))

    def money(value):
        return "INR {:,.2f}".format(float(value))

    story = [
        Paragraph("MSME Credit Readiness Review", styles["ReportTitle"]),
        Paragraph("Business: " + _safe(business_name), styles["BodyText"]),
        Paragraph("Report generated: " + date.today().isoformat(), styles["BodyText"]),
        Paragraph("Latest reporting month: " + _safe(result["latest_month"]), styles["BodyText"]),
        Spacer(1, 4 * mm),
        Paragraph("Review outcome", styles["Section"]),
        Paragraph("<b>" + _safe(result["status"]) + "</b>", styles["BodyText"]),
        Paragraph(
            "This is an explainable cash-flow planning review, not a bureau score, "
            "default prediction, lender rating or loan approval.",
            styles["SmallNote"],
        ),
        Paragraph("Key indicators", styles["Section"]),
    ]
    coverage = (
        "Not calculated" if result["coverage_proxy"] is None
        else "{:.2f}x".format(float(result["coverage_proxy"]))
    )
    revenue_change = (
        "Not available" if result["revenue_change_percent"] is None
        else "{:+.2f}%".format(float(result["revenue_change_percent"]))
    )
    rows = [
        ["Indicator", "Result"],
        ["Latest cash headroom", money(result["latest_cash_headroom"])],
        ["Average headroom (latest 3 months)", money(result["average_three_month_headroom"])],
        ["Proposed additional monthly EMI", money(result["proposed_monthly_emi"])],
        ["Headroom after proposed EMI", money(result["headroom_after_proposed_emi"])],
        ["Months with non-negative headroom", "{}/3".format(result["positive_headroom_months"])],
        ["Simplified coverage proxy", coverage],
        ["Latest revenue movement", revenue_change],
        ["Months reviewed", ", ".join(str(m) for m in result["months_reviewed"])],
    ]
    table = Table(rows, colWidths=[105 * mm, 65 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eefc")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#172554")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([table, Paragraph("Explainable findings", styles["Section"])])
    story.extend(_bullet_list(result["findings"], styles))
    story.append(Paragraph("Evidence gaps", styles["Section"]))
    story.extend(_bullet_list(result["evidence_gaps"], styles))
    story.extend([
        Paragraph("Methodology and limitations", styles["Section"]),
        Paragraph(_safe(result["limitations"]), styles["SmallNote"]),
        Spacer(1, 3 * mm),
        Paragraph(
            "Prepared from user-entered records. Verify all figures against source "
            "documents. This report does not verify bank statements, credit bureau "
            "data, collateral, statutory compliance or lender policy.",
            styles["SmallNote"],
        ),
    ])

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(18 * mm, 10 * mm, "MSME Financial Platform | For planning purposes")
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, "Page {}".format(document.page))
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()


def _safe(value):
    from xml.sax.saxutils import escape
    return escape(str(value))


def _bullet_list(items, styles):
    if not items:
        items = ["None recorded."]
    return [
        KeepTogether([
            Paragraph("• " + _safe(item), styles["BodyText"]),
            Spacer(1, 1.5 * mm),
        ])
        for item in items
    ]
