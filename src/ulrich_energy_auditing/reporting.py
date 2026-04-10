from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from ulrich_energy_auditing.models import AuditInput, AuditSummary


def _report_sections(audit: AuditInput, summary: AuditSummary) -> list[tuple[str, list[str]]]:
    recommendations = [
        f"{item.title} ({item.priority} priority): {item.reason} Estimated annual savings: ${item.estimated_annual_savings_usd}."
        for item in summary.recommendations
    ]
    notes = audit.notes if audit.notes else ["None recorded."]
    if not recommendations:
        recommendations = ["No immediate upgrade recommendations triggered by the current rule set."]

    return [
        (
            "Property",
            [
                f"Client: {audit.building.client_name}",
                f"Address: {audit.building.address}",
                f"Type: {audit.building.building_type}",
                f"Square feet: {audit.building.square_feet}",
                f"Year built: {audit.building.year_built}",
            ],
        ),
        (
            "Baseline",
            [
                f"Energy use intensity: {summary.energy_use_intensity} kBtu/sqft/year",
                f"Benchmark band: {summary.benchmark_band}",
                f"Estimated annual opportunity: ${summary.estimated_total_annual_savings_usd}",
            ],
        ),
        (
            "Regional Benchmark",
            [
                f"Benchmark pack: {summary.benchmark_comparison.pack.label}. "
                f"{summary.benchmark_comparison.selection_reason}",
                f"Peer position: {summary.benchmark_comparison.performance_summary} "
                f"{summary.benchmark_comparison.peer_targets_summary}",
                "Envelope targets: "
                + " ".join(summary.benchmark_comparison.system_notes),
            ],
        ),
        (
            "Systems Snapshot",
            [
                f"HVAC age: {audit.systems.hvac_age_years} years",
                f"Water heater age: {audit.systems.water_heater_age_years} years",
                f"Attic insulation: R-{audit.systems.attic_insulation_r_value}",
                f"Blower door: {audit.systems.blower_door_ach50} ACH50",
                f"Duct leakage: {audit.systems.duct_leakage_percent}%",
            ],
        ),
        ("Recommendations", recommendations),
        ("Field Notes", notes),
    ]


def _pdf_report_sections(audit: AuditInput, summary: AuditSummary) -> list[tuple[str, list[str]]]:
    recommendations = [
        f"{item.title} ({item.priority} priority) | est. annual savings ${item.estimated_annual_savings_usd}"
        for item in summary.recommendations
    ]
    notes = audit.notes if audit.notes else ["None recorded."]
    if not recommendations:
        recommendations = ["No immediate upgrade recommendations triggered by the current rule set."]

    return [
        (
            "Property",
            [
                f"Client: {audit.building.client_name}",
                f"Address: {audit.building.address}",
                f"Type: {audit.building.building_type} | {audit.building.square_feet} sqft | built {audit.building.year_built}",
            ],
        ),
        (
            "Baseline",
            [
                f"EUI: {summary.energy_use_intensity} kBtu/sqft/year | band: {summary.benchmark_band}",
                f"Estimated annual opportunity: ${summary.estimated_total_annual_savings_usd}",
            ],
        ),
        (
            "Regional Benchmark",
            [
                f"{summary.benchmark_comparison.pack.label} | {summary.benchmark_comparison.performance_summary}",
                "Envelope targets: " + " ".join(summary.benchmark_comparison.system_notes),
            ],
        ),
        (
            "Systems Snapshot",
            [
                f"HVAC {audit.systems.hvac_age_years} yrs | Water heater {audit.systems.water_heater_age_years} yrs",
                f"Attic R-{audit.systems.attic_insulation_r_value} | Blower door {audit.systems.blower_door_ach50} ACH50 | Duct leakage {audit.systems.duct_leakage_percent}%",
            ],
        ),
        ("Recommendations", recommendations),
        ("Field Notes", notes),
    ]


def render_markdown_report(audit: AuditInput, summary: AuditSummary) -> str:
    rendered_sections = []
    for title, items in _report_sections(audit, summary):
        body = "\n".join([f"- {item}" for item in items])
        rendered_sections.append(f"## {title}\n\n{body}")

    return "# Energy Audit Report\n\n" + "\n\n".join(rendered_sections) + "\n"


def write_pdf_report(audit: AuditInput, summary: AuditSummary, output_path: Path) -> None:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "AuditTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        spaceAfter=6,
        textColor=colors.HexColor("#17324D"),
    )
    subtitle_style = ParagraphStyle(
        "AuditSubtitle",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=10,
    )
    heading_style = ParagraphStyle(
        "AuditHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        spaceBefore=6,
        spaceAfter=4,
        textColor=colors.HexColor("#17324D"),
    )
    bullet_style = ParagraphStyle(
        "AuditBullet",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=11,
        leftIndent=14,
        firstLineIndent=0,
        spaceAfter=2,
    )

    story = [
        Paragraph("Energy Audit Report", title_style),
        Paragraph(
            escape(f"{audit.building.client_name} | {audit.building.address}"),
            subtitle_style,
        ),
    ]

    sections = _pdf_report_sections(audit, summary)
    for index, (title, items) in enumerate(sections):
        story.append(Paragraph(escape(title), heading_style))
        for item in items:
            story.append(Paragraph(escape(item), bullet_style, bulletText="-"))
        if index < len(sections) - 1:
            story.append(Spacer(1, 6))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=42,
        rightMargin=42,
        topMargin=46,
        bottomMargin=34,
        title="Energy Audit Report",
        author="Ulrich Energy Auditing",
    )
    document.build(story, onFirstPage=_draw_page_chrome, onLaterPages=_draw_page_chrome)


def _draw_page_chrome(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D0D7DE"))
    canvas.line(doc.leftMargin, letter[1] - 36, letter[0] - doc.rightMargin, letter[1] - 36)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.drawString(doc.leftMargin, 24, "Ulrich Energy Auditing")
    canvas.drawRightString(letter[0] - doc.rightMargin, 24, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()
