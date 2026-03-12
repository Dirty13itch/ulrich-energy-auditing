from __future__ import annotations

from ulrich_energy_auditing.models import AuditInput, AuditSummary


def render_markdown_report(audit: AuditInput, summary: AuditSummary) -> str:
    recommendations = "\n".join(
        [
            f"- **{item.title}** ({item.priority} priority): {item.reason} Estimated annual savings: ${item.estimated_annual_savings_usd}."
            for item in summary.recommendations
        ]
    )
    notes = "\n".join([f"- {note}" for note in audit.notes]) if audit.notes else "- None recorded."
    if not recommendations:
        recommendations = "- No immediate upgrade recommendations triggered by the current rule set."

    return f"""# Energy Audit Report

## Property

- Client: {audit.building.client_name}
- Address: {audit.building.address}
- Type: {audit.building.building_type}
- Square feet: {audit.building.square_feet}
- Year built: {audit.building.year_built}

## Baseline

- Energy use intensity: {summary.energy_use_intensity} kBtu/sqft/year
- Benchmark band: {summary.benchmark_band}
- Estimated annual opportunity: ${summary.estimated_total_annual_savings_usd}

## Systems Snapshot

- HVAC age: {audit.systems.hvac_age_years} years
- Water heater age: {audit.systems.water_heater_age_years} years
- Attic insulation: R-{audit.systems.attic_insulation_r_value}
- Blower door: {audit.systems.blower_door_ach50} ACH50
- Duct leakage: {audit.systems.duct_leakage_percent}%

## Recommendations

{recommendations}

## Field Notes

{notes}
"""
