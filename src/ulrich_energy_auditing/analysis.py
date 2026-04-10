from __future__ import annotations

from ulrich_energy_auditing.benchmark_packs import resolve_benchmark_pack
from ulrich_energy_auditing.models import (
    AuditInput,
    AuditSummary,
    BenchmarkComparison,
    BenchmarkPack,
    Recommendation,
)


def _benchmark_band(eui: float, pack: BenchmarkPack) -> str:
    if eui <= pack.high_performing_max_eui:
        return "high-performing"
    if eui <= pack.solid_max_eui:
        return "solid"
    if eui <= pack.improvement_ready_max_eui:
        return "improvement-ready"
    return "high-opportunity"


def _build_benchmark_comparison(
    audit: AuditInput,
    *,
    eui: float,
    pack: BenchmarkPack,
    benchmark_band: str,
    selection_reason: str,
) -> BenchmarkComparison:
    if benchmark_band == "high-performing":
        performance_summary = (
            f"This property lands inside the high-performing range for the {pack.label} peer group."
        )
    elif benchmark_band == "solid":
        gap = round(eui - pack.high_performing_max_eui, 1)
        performance_summary = (
            f"This property is in the solid range and sits {gap} kBtu/sqft/year above the "
            f"high-performing ceiling for the {pack.label} peer group."
        )
    elif benchmark_band == "improvement-ready":
        gap = round(eui - pack.solid_max_eui, 1)
        performance_summary = (
            f"This property is in the improvement-ready range and runs {gap} kBtu/sqft/year above "
            f"the solid-band ceiling for the {pack.label} peer group."
        )
    else:
        gap = round(eui - pack.improvement_ready_max_eui, 1)
        performance_summary = (
            f"This property is a high-opportunity site and runs {gap} kBtu/sqft/year above the "
            f"improvement-ready ceiling for the {pack.label} peer group."
        )

    peer_targets_summary = (
        f"Pack thresholds: high-performing <= {pack.high_performing_max_eui} kBtu/sqft/year, "
        f"solid <= {pack.solid_max_eui}, improvement-ready <= {pack.improvement_ready_max_eui}."
    )

    insulation_gap = pack.attic_insulation_target_r - audit.systems.attic_insulation_r_value
    system_notes = [
        _insulation_gap_line(
            current_r_value=audit.systems.attic_insulation_r_value,
            target_r_value=pack.attic_insulation_target_r,
            gap=insulation_gap,
        ),
        _blower_gap_line(
            current_ach50=audit.systems.blower_door_ach50,
            target_ach50=pack.blower_door_target_ach50,
        ),
        _duct_gap_line(
            current_percent=audit.systems.duct_leakage_percent,
            target_percent=pack.duct_leakage_target_percent,
        ),
    ]

    return BenchmarkComparison(
        pack=pack,
        selection_reason=selection_reason,
        performance_summary=performance_summary,
        peer_targets_summary=peer_targets_summary,
        system_notes=system_notes,
    )


def _insulation_gap_line(*, current_r_value: int, target_r_value: int, gap: int) -> str:
    if gap > 0:
        return (
            f"Attic insulation is R-{current_r_value}, which is R-{gap} below the pack target "
            f"of R-{target_r_value}."
        )
    if gap < 0:
        return (
            f"Attic insulation is R-{current_r_value}, which is R-{abs(gap)} above the pack target "
            f"of R-{target_r_value}."
        )
    return f"Attic insulation is R-{current_r_value}, matching the pack target of R-{target_r_value}."


def _blower_gap_line(*, current_ach50: float, target_ach50: float) -> str:
    gap = round(current_ach50 - target_ach50, 1)
    if gap > 0:
        return (
            f"Blower-door leakage is {current_ach50} ACH50, which is {gap:g} ACH50 leakier than "
            f"the pack target of {target_ach50} ACH50."
        )
    if gap < 0:
        return (
            f"Blower-door leakage is {current_ach50} ACH50, which is {abs(gap):g} ACH50 tighter than "
            f"the pack target of {target_ach50} ACH50."
        )
    return f"Blower-door leakage is {current_ach50} ACH50, matching the pack target of {target_ach50} ACH50."


def _duct_gap_line(*, current_percent: float, target_percent: float) -> str:
    gap = round(current_percent - target_percent, 1)
    if gap > 0:
        return (
            f"Duct leakage is {current_percent}%, which is {gap:g} points worse than the pack target "
            f"of {target_percent}%."
        )
    if gap < 0:
        return (
            f"Duct leakage is {current_percent}%, which is {abs(gap):g} points better than the pack target "
            f"of {target_percent}%."
        )
    return f"Duct leakage is {current_percent}%, matching the pack target of {target_percent}%."


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


def analyze_audit(audit: AuditInput, benchmark_pack_id: str | None = None) -> AuditSummary:
    source_energy_kbtu = (audit.consumption.annual_electric_kwh * 3.412) + (
        audit.consumption.annual_gas_therms * 100
    )
    eui = round(source_energy_kbtu / audit.building.square_feet, 2)
    benchmark_pack, selection_reason = resolve_benchmark_pack(
        audit.building,
        benchmark_pack_id=benchmark_pack_id,
    )
    benchmark_band = _benchmark_band(eui, benchmark_pack)
    recommendations = _recommendations(audit)
    total_savings = sum(item.estimated_annual_savings_usd for item in recommendations)
    return AuditSummary(
        energy_use_intensity=eui,
        benchmark_band=benchmark_band,
        benchmark_comparison=_build_benchmark_comparison(
            audit,
            eui=eui,
            pack=benchmark_pack,
            benchmark_band=benchmark_band,
            selection_reason=selection_reason,
        ),
        recommendations=recommendations,
        estimated_total_annual_savings_usd=total_savings,
    )
