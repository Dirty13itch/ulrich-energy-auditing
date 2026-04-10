import json
import os
from pathlib import Path

from pypdf import PdfReader

from ulrich_energy_auditing.guided_intake import (
    GuidedIntakeOptions,
    process_guided_intake_submission,
)


def test_process_guided_intake_submission_generates_outputs_and_history(tmp_path: Path) -> None:
    local_app_data = tmp_path / "localappdata"
    original_local_app_data = os.environ.get("LOCALAPPDATA")
    os.environ["LOCALAPPDATA"] = str(local_app_data)
    try:
        options = GuidedIntakeOptions(
            emit_json_path=tmp_path / "reports" / "guided-audit.json",
            output_path=tmp_path / "reports" / "guided-report.md",
            pdf_output_path=tmp_path / "reports" / "guided-report.pdf",
            benchmark_pack_id=None,
            save_name=None,
            open_browser=False,
        )

        result = process_guided_intake_submission(
            {
                "audit": {
                    "building": {
                        "client_name": "Guided Intake Sample",
                        "address": "123 Main St, Minneapolis, MN 55401",
                        "building_type": "residential",
                        "square_feet": 2400,
                        "year_built": 1996,
                    },
                    "systems": {
                        "hvac_age_years": 16,
                        "water_heater_age_years": 7,
                        "attic_insulation_r_value": 30,
                        "blower_door_ach50": 6.2,
                        "duct_leakage_percent": 15.0,
                    },
                    "consumption": {
                        "annual_electric_kwh": 12000,
                        "annual_gas_therms": 400,
                    },
                    "notes": ["Ice dam history", "Attic hatch needs weatherstripping"],
                },
                "utility_bills_csv": (
                    "billing_month,electric_kwh,gas_therms\n"
                    "2025-01,1200,48\n"
                    "2025-02,1100,43\n"
                ),
                "save_name": "Guided bundle",
            },
            options=options,
        )
    finally:
        if original_local_app_data is None:
            os.environ.pop("LOCALAPPDATA", None)
        else:
            os.environ["LOCALAPPDATA"] = original_local_app_data

    normalized_payload = json.loads(options.emit_json_path.read_text(encoding="utf-8"))
    assert normalized_payload["consumption"]["annual_electric_kwh"] == 2300
    assert normalized_payload["consumption"]["annual_gas_therms"] == 91
    assert "cold-residential-legacy" == result["benchmark_pack_id"]
    assert result["saved_bundle_dir"] is not None

    report_markdown = options.output_path.read_text(encoding="utf-8")
    assert "Guided Intake Sample" in report_markdown
    assert "Regional Benchmark" in report_markdown

    reader = PdfReader(str(options.pdf_output_path))
    assert len(reader.pages) == 1

    index_path = local_app_data / "UlrichEnergyAuditing" / "saved-audits" / "index.json"
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert index_payload[0]["input_source"] == "guided-intake+utility-bills"
