"""Generates the paid PDF report using ReportLab (pure Python, no system
package dependencies like Cairo/Pango — keeps this deployable on Render's
default Python build without extra buildpacks).
"""

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BRAND_GREEN = colors.HexColor("#16a34a")
BRAND_DARK = colors.HexColor("#0e7a37")
MUTED = colors.HexColor("#4b5563")


def _naira(value: float) -> str:
    return f"N{value:,.2f}"


def generate_report_pdf(*, result: dict, disco_name: str, band: str, customer_type: str, scenario: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        title="WattAmIUsing Electricity Cost Report",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleGreen", parent=styles["Title"], textColor=BRAND_GREEN, fontSize=20)
    heading_style = ParagraphStyle("Heading", parent=styles["Heading2"], textColor=BRAND_DARK, spaceBefore=14)
    body_style = ParagraphStyle("BodyMuted", parent=styles["Normal"], textColor=MUTED, fontSize=10)

    story = [
        Paragraph("WattAmIUsing — Electricity Cost Report", title_style),
        Paragraph(
            f"{disco_name} · Band {band} · {customer_type.replace('_', ' ').upper()} · "
            f"{scenario.title()} day scenario",
            body_style,
        ),
        Paragraph(f"Generated {datetime.now().strftime('%d %B %Y, %H:%M')}", body_style),
        Spacer(1, 10 * mm),
    ]

    # Totals summary
    totals = result["totals"]
    summary_rows = [
        ["Daily", _naira(totals["daily_cost"]), f"{totals['daily_kwh']:.2f} kWh"],
        ["Weekly", _naira(totals["weekly_cost"]), "—"],
        ["Monthly", _naira(totals["monthly_cost"]), f"{totals['monthly_kwh']:.2f} kWh"],
        ["Yearly", _naira(totals["yearly_cost"]), "—"],
    ]
    story.append(Paragraph("Cost Summary", heading_style))
    summary_table = Table([["Period", "Cost", "Units"], *summary_rows], colWidths=[50 * mm, 60 * mm, 60 * mm])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BRAND_GREEN),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e9e7")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8f7")]),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(summary_table)

    # Appliance breakdown
    story.append(Paragraph("Appliance Breakdown", heading_style))
    item_rows = [
        [
            item["name"],
            f"{item['watts']:.0f} W",
            str(item["quantity"]),
            f"{item['hours_per_day']:.1f} h",
            f"{item['kwh_per_day']:.2f} kWh",
            _naira(item["cost_per_day"]),
        ]
        for item in result["items"]
    ]
    item_table = Table(
        [["Appliance", "Watts", "Qty", "Hrs/day", "kWh/day", "Cost/day"], *item_rows],
        colWidths=[45 * mm, 20 * mm, 15 * mm, 20 * mm, 25 * mm, 25 * mm],
    )
    item_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e9e7")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8f7")]),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(item_table)

    # Highest consumers
    if result.get("ranking"):
        story.append(Paragraph("Highest Consumers", heading_style))
        for r in result["ranking"]:
            story.append(Paragraph(f"• {r['name']} — {r['share_pct']}% of total usage", body_style))

    # Insights
    if result.get("insights"):
        story.append(Paragraph("Insights", heading_style))
        for insight in result["insights"]:
            story.append(Paragraph(f"💡 {insight}", body_style))

    story.append(Spacer(1, 10 * mm))
    story.append(
        Paragraph(
            "This is an estimate based on NERC-published tariff rates and the appliance details you "
            "provided. Actual bills may vary based on meter type, fees, and other charges.",
            body_style,
        )
    )

    doc.build(story)
    return buffer.getvalue()
