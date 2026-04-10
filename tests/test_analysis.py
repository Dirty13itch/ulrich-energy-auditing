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

    assert summary.energy_use_intensity > 0
    assert summary.benchmark_band in {
        "high-performing",
        "solid",
        "improvement-ready",
        "high-opportunity",
    }
    assert summary.benchmark_comparison.pack.pack_id == "mixed-humid-residential-legacy"
    assert "Mixed-Humid Residential Retrofit" in summary.benchmark_comparison.pack.label
    assert summary.benchmark_comparison.system_notes
    assert summary.recommendations
    assert summary.estimated_total_annual_savings_usd > 0
