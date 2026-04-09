import json
from pathlib import Path

from ulrich_energy_auditing.analysis import analyze_audit
from ulrich_energy_auditing.models import AuditInput, BuildingProfile, BuildingSystems, ConsumptionProfile


def test_analysis_generates_recommendations() -> None:
    audit = AuditInput(
        building=BuildingProfile(
            client_name="Test Client",
            address="123 Test St",
            building_type="residential",
            square_feet=2000,
            year_built=2001,
        ),
        systems=BuildingSystems(
            hvac_age_years=18,
            water_heater_age_years=13,
            attic_insulation_r_value=19,
            blower_door_ach50=6.1,
            duct_leakage_percent=17,
        ),
        consumption=ConsumptionProfile(
            annual_electric_kwh=15000,
            annual_gas_therms=540,
        ),
        notes=["Comfort complaints upstairs."],
    )

    summary = analyze_audit(audit)

    assert summary.energy_use_intensity == 52.59
    assert summary.benchmark_band == "high-opportunity"
    assert [(item.title, item.priority, item.estimated_annual_savings_usd) for item in summary.recommendations] == [
        ("Increase attic insulation", "high", 450),
        ("Air sealing package", "high", 380),
        ("HVAC tune-up or replacement planning", "medium", 520),
        ("Duct sealing and balancing", "medium", 260),
        ("Water heater replacement planning", "low", 140),
    ]
    assert summary.estimated_total_annual_savings_usd == 1750


def test_analysis_respects_threshold_boundaries() -> None:
    audit = AuditInput(
        building=BuildingProfile(
            client_name="Threshold Client",
            address="456 Boundary Ave",
            building_type="residential",
            square_feet=2000,
            year_built=2005,
        ),
        systems=BuildingSystems(
            hvac_age_years=14,
            water_heater_age_years=11,
            attic_insulation_r_value=38,
            blower_door_ach50=5.0,
            duct_leakage_percent=14.9,
        ),
        consumption=ConsumptionProfile(
            annual_electric_kwh=4000,
            annual_gas_therms=20,
        ),
        notes=[],
    )

    summary = analyze_audit(audit)

    assert summary.energy_use_intensity == 7.82
    assert summary.benchmark_band == "high-performing"
    assert summary.recommendations == []
    assert summary.estimated_total_annual_savings_usd == 0


def test_sample_audit_summary_matches_repo_contract() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    payload = json.loads((repo_root / "examples" / "sample_audit.json").read_text(encoding="utf-8"))
    audit = AuditInput(
        building=BuildingProfile(**payload["building"]),
        systems=BuildingSystems(**payload["systems"]),
        consumption=ConsumptionProfile(**payload["consumption"]),
        notes=payload["notes"],
    )

    summary = analyze_audit(audit)

    assert summary.energy_use_intensity == 49.72
    assert summary.benchmark_band == "high-opportunity"
    assert [item.title for item in summary.recommendations] == [
        "Increase attic insulation",
        "Air sealing package",
        "HVAC tune-up or replacement planning",
        "Duct sealing and balancing",
        "Water heater replacement planning",
    ]
    assert summary.estimated_total_annual_savings_usd == 1750
