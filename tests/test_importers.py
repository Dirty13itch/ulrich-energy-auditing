import json
from pathlib import Path

import pytest

from ulrich_energy_auditing.importers import (
    audit_to_payload,
    load_audit,
    load_utility_bills,
)


def test_load_audit_from_csv_and_utility_bills() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    audit = load_audit(
        repo_root / "examples" / "sample_audit.csv",
        utility_bills_path=repo_root / "examples" / "sample_utility_bills.csv",
    )

    assert audit.building.client_name == "Ulrich Sample Residence"
    assert audit.systems.hvac_age_years == 17
    assert audit.consumption.annual_electric_kwh == 16800
    assert audit.consumption.annual_gas_therms == 620
    assert len(audit.notes) == 2


def test_utility_bills_override_existing_consumption_values(tmp_path: Path) -> None:
    payload = {
        "building": {
            "client_name": "CSV Override Test",
            "address": "1 Main St",
            "building_type": "residential",
            "square_feet": 1800,
            "year_built": 2005,
        },
        "systems": {
            "hvac_age_years": 8,
            "water_heater_age_years": 4,
            "attic_insulation_r_value": 49,
            "blower_door_ach50": 4.1,
            "duct_leakage_percent": 9,
        },
        "consumption": {
            "annual_electric_kwh": 999,
            "annual_gas_therms": 999,
        },
        "notes": [],
    }
    json_path = tmp_path / "audit.json"
    json_path.write_text(json.dumps(payload), encoding="utf-8")

    bills_path = tmp_path / "utility_bills.csv"
    bills_path.write_text(
        "billing_month,electric_kwh,gas_therms\n"
        "2025-01,1000,40\n"
        "2025-02,900,35\n",
        encoding="utf-8",
    )

    audit = load_audit(json_path, utility_bills_path=bills_path)

    assert audit.consumption.annual_electric_kwh == 1900
    assert audit.consumption.annual_gas_therms == 75


def test_load_utility_bills_requires_supported_usage_column(tmp_path: Path) -> None:
    bills_path = tmp_path / "utility_bills.csv"
    bills_path.write_text("billing_month,total_cost\n2025-01,220.13\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Utility bill CSV must include at least one electric or gas usage column"):
        load_utility_bills(bills_path)


def test_audit_to_payload_round_trips_notes_and_consumption() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    audit = load_audit(
        repo_root / "examples" / "sample_audit.csv",
        utility_bills_path=repo_root / "examples" / "sample_utility_bills.csv",
    )

    payload = audit_to_payload(audit)

    assert payload["notes"][0].startswith("South-facing rooms")
    assert payload["consumption"]["annual_electric_kwh"] == 16800
