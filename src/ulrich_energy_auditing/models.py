from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BuildingProfile:
    client_name: str
    address: str
    building_type: str
    square_feet: int
    year_built: int


@dataclass(slots=True)
class BuildingSystems:
    hvac_age_years: int
    water_heater_age_years: int
    attic_insulation_r_value: int
    blower_door_ach50: float
    duct_leakage_percent: float


@dataclass(slots=True)
class ConsumptionProfile:
    annual_electric_kwh: float
    annual_gas_therms: float


@dataclass(slots=True)
class AuditInput:
    building: BuildingProfile
    systems: BuildingSystems
    consumption: ConsumptionProfile
    notes: list[str]


@dataclass(slots=True)
class Recommendation:
    title: str
    reason: str
    estimated_annual_savings_usd: int
    priority: str


@dataclass(slots=True)
class BenchmarkPack:
    pack_id: str
    label: str
    region: str
    building_archetype: str
    vintage_label: str
    description: str
    high_performing_max_eui: float
    solid_max_eui: float
    improvement_ready_max_eui: float
    attic_insulation_target_r: int
    blower_door_target_ach50: float
    duct_leakage_target_percent: float


@dataclass(slots=True)
class BenchmarkComparison:
    pack: BenchmarkPack
    selection_reason: str
    performance_summary: str
    peer_targets_summary: str
    system_notes: list[str]


@dataclass(slots=True)
class AuditSummary:
    energy_use_intensity: float
    benchmark_band: str
    benchmark_comparison: BenchmarkComparison
    recommendations: list[Recommendation]
    estimated_total_annual_savings_usd: int
