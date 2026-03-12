from __future__ import annotations

from ulrich_energy_auditing.models import AuditInput, AuditSummary, Recommendation


def _benchmark_band(eui: float) -> str:
    if eui < 8:
        return "high-performing"
    if eui < 12:
        return "solid"
    if eui < 16:
        return "improvement-ready"
    return "high-opportunity"


def _recommendations(audit: AuditInput) -> list[Recommendation]:
    systems = audit.systems
    items: list[Recommendation] = []

    if systems.attic_insulation_r_value < 38:
        items.append(
            Recommendation(
                title="Increase attic insulation",
                reason="Current attic insulation is below a typical modern target for comfort and load reduction.",
                estimated_annual_savings_usd=450,
                priority="high",
            )
        )

    if systems.blower_door_ach50 > 5:
        items.append(
            Recommendation(
                title="Air sealing package",
                reason="Blower-door leakage suggests envelope leakage is materially increasing heating and cooling demand.",
                estimated_annual_savings_usd=380,
                priority="high",
            )
        )

    if systems.hvac_age_years >= 15:
        items.append(
            Recommendation(
                title="HVAC tune-up or replacement planning",
                reason="The HVAC system is in late-life territory and likely below current efficiency expectations.",
                estimated_annual_savings_usd=520,
                priority="medium",
            )
        )

    if systems.duct_leakage_percent >= 15:
        items.append(
            Recommendation(
                title="Duct sealing and balancing",
                reason="Observed duct leakage is high enough to drive comfort issues and system waste.",
                estimated_annual_savings_usd=260,
                priority="medium",
            )
        )

    if systems.water_heater_age_years >= 12:
        items.append(
            Recommendation(
                title="Water heater replacement planning",
                reason="The water heater is entering replacement territory and may benefit from efficiency upgrades.",
                estimated_annual_savings_usd=140,
                priority="low",
            )
        )

    return items


def analyze_audit(audit: AuditInput) -> AuditSummary:
    source_energy_kbtu = (audit.consumption.annual_electric_kwh * 3.412) + (
        audit.consumption.annual_gas_therms * 100
    )
    eui = round(source_energy_kbtu / audit.building.square_feet, 2)
    recommendations = _recommendations(audit)
    total_savings = sum(item.estimated_annual_savings_usd for item in recommendations)
    return AuditSummary(
        energy_use_intensity=eui,
        benchmark_band=_benchmark_band(eui),
        recommendations=recommendations,
        estimated_total_annual_savings_usd=total_savings,
    )
