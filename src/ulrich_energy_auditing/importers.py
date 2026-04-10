from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

from ulrich_energy_auditing.models import (
    AuditInput,
    BuildingProfile,
    BuildingSystems,
    ConsumptionProfile,
)

_FIELD_CASTERS: dict[str, dict[str, type[int] | type[float] | type[str]]] = {
    "building": {
        "client_name": str,
        "address": str,
        "building_type": str,
        "square_feet": int,
        "year_built": int,
    },
    "systems": {
        "hvac_age_years": int,
        "water_heater_age_years": int,
        "attic_insulation_r_value": int,
        "blower_door_ach50": float,
        "duct_leakage_percent": float,
    },
    "consumption": {
        "annual_electric_kwh": float,
        "annual_gas_therms": float,
    },
}

_NOTE_FIELDS = {"note", "text", "value"}
_ELECTRIC_FIELDS = ("electric_kwh", "annual_electric_kwh", "kwh")
_GAS_FIELDS = ("gas_therms", "annual_gas_therms", "therms")


def load_audit(path: Path, utility_bills_path: Path | None = None) -> AuditInput:
    payload = load_audit_payload(path)
    if utility_bills_path is not None:
        payload["consumption"] = _consumption_to_payload(load_utility_bills(utility_bills_path))
    return build_audit_input(payload)


def load_audit_payload(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return _load_json_payload(path)
    if suffix == ".csv":
        return _load_csv_payload(path)
    raise ValueError(f"Unsupported audit input format for {path.name}. Use .json or .csv.")


def load_utility_bills(path: Path) -> ConsumptionProfile:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return _load_utility_bills_from_handle(handle)


def load_utility_bills_text(csv_text: str) -> ConsumptionProfile:
    with io.StringIO(csv_text.lstrip("\ufeff")) as handle:
        return _load_utility_bills_from_handle(handle)


def build_audit_input(payload: dict[str, Any]) -> AuditInput:
    building = payload.get("building", {})
    systems = payload.get("systems", {})
    consumption = payload.get("consumption", {})
    notes = payload.get("notes", [])

    _assert_required_fields("building", building)
    _assert_required_fields("systems", systems)
    _assert_required_fields("consumption", consumption)

    return AuditInput(
        building=BuildingProfile(**building),
        systems=BuildingSystems(**systems),
        consumption=ConsumptionProfile(**consumption),
        notes=list(notes),
    )


def audit_to_payload(audit: AuditInput) -> dict[str, Any]:
    return {
        "building": {
            "client_name": audit.building.client_name,
            "address": audit.building.address,
            "building_type": audit.building.building_type,
            "square_feet": audit.building.square_feet,
            "year_built": audit.building.year_built,
        },
        "systems": {
            "hvac_age_years": audit.systems.hvac_age_years,
            "water_heater_age_years": audit.systems.water_heater_age_years,
            "attic_insulation_r_value": audit.systems.attic_insulation_r_value,
            "blower_door_ach50": audit.systems.blower_door_ach50,
            "duct_leakage_percent": audit.systems.duct_leakage_percent,
        },
        "consumption": _consumption_to_payload(audit.consumption),
        "notes": list(audit.notes),
    }


def write_audit_json(audit: AuditInput, path: Path) -> None:
    path.write_text(json.dumps(audit_to_payload(audit), indent=2) + "\n", encoding="utf-8")


def _load_json_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Audit JSON in {path.name} must contain an object at the top level.")
    return payload


def _load_csv_payload(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or ())
        required_headers = {"section", "field", "value"}
        if not required_headers.issubset(fieldnames):
            raise ValueError(
                f"Audit CSV {path.name} must include headers: {', '.join(sorted(required_headers))}."
            )

        payload: dict[str, Any] = {
            "building": {},
            "systems": {},
            "consumption": {},
            "notes": [],
        }

        for line_number, row in enumerate(reader, start=2):
            section = (row.get("section") or "").strip().lower()
            field = (row.get("field") or "").strip()
            raw_value = (row.get("value") or "").strip()

            if not section:
                raise ValueError(f"Missing section in audit CSV at line {line_number}.")
            if not field:
                raise ValueError(f"Missing field name in audit CSV at line {line_number}.")

            if section == "notes":
                if field.lower() not in _NOTE_FIELDS:
                    raise ValueError(
                        f"Unsupported notes field '{field}' in audit CSV at line {line_number}. "
                        "Use note, text, or value."
                    )
                if raw_value:
                    payload["notes"].append(raw_value)
                continue

            if section not in _FIELD_CASTERS:
                raise ValueError(
                    f"Unsupported section '{section}' in audit CSV at line {line_number}. "
                    "Use building, systems, consumption, or notes."
                )

            casters = _FIELD_CASTERS[section]
            if field not in casters:
                valid_fields = ", ".join(sorted(casters))
                raise ValueError(
                    f"Unsupported field '{field}' in section '{section}' at line {line_number}. "
                    f"Valid fields: {valid_fields}."
                )
            if not raw_value:
                raise ValueError(f"Missing value for {section}.{field} at line {line_number}.")
            if field in payload[section]:
                raise ValueError(
                    f"Duplicate field {section}.{field} in audit CSV at line {line_number}."
                )

            payload[section][field] = _cast_value(
                raw_value,
                casters[field],
                section=section,
                field_name=field,
                line_number=line_number,
            )

    return payload


def _cast_value(
    raw_value: str,
    caster: type[int] | type[float] | type[str],
    *,
    section: str,
    field_name: str,
    line_number: int,
) -> int | float | str:
    try:
        return caster(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"Invalid value '{raw_value}' for {section}.{field_name} at line {line_number}."
        ) from exc


def _assert_required_fields(section: str, values: dict[str, Any]) -> None:
    missing = [field for field in _FIELD_CASTERS[section] if field not in values]
    if missing:
        raise ValueError(
            f"Missing required {section} fields: {', '.join(sorted(missing))}."
        )


def _consumption_to_payload(consumption: ConsumptionProfile) -> dict[str, float]:
    return {
        "annual_electric_kwh": consumption.annual_electric_kwh,
        "annual_gas_therms": consumption.annual_gas_therms,
    }


def _find_first_present(fieldnames: tuple[str, ...], candidates: tuple[str, ...]) -> str | None:
    lowered = {field.lower(): field for field in fieldnames}
    for candidate in candidates:
        if candidate in lowered:
            return lowered[candidate]
    return None


def _parse_optional_float(raw_value: str, *, line_number: int, field_name: str) -> float:
    value = raw_value.strip()
    if not value:
        return 0.0
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(
            f"Invalid numeric value '{raw_value}' for utility bill field {field_name} at line {line_number}."
        ) from exc


def _load_utility_bills_from_handle(handle: io.TextIOBase) -> ConsumptionProfile:
    reader = csv.DictReader(handle)
    fieldnames = tuple(reader.fieldnames or ())
    electric_field = _find_first_present(fieldnames, _ELECTRIC_FIELDS)
    gas_field = _find_first_present(fieldnames, _GAS_FIELDS)

    if electric_field is None and gas_field is None:
        raise ValueError(
            "Utility bill CSV must include at least one electric or gas usage column. "
            "Supported headers include electric_kwh, annual_electric_kwh, gas_therms, and annual_gas_therms."
        )

    annual_electric_kwh = 0.0
    annual_gas_therms = 0.0
    for line_number, row in enumerate(reader, start=2):
        if electric_field is not None:
            annual_electric_kwh += _parse_optional_float(
                row.get(electric_field, ""),
                line_number=line_number,
                field_name=electric_field,
            )
        if gas_field is not None:
            annual_gas_therms += _parse_optional_float(
                row.get(gas_field, ""),
                line_number=line_number,
                field_name=gas_field,
            )

    return ConsumptionProfile(
        annual_electric_kwh=round(annual_electric_kwh, 2),
        annual_gas_therms=round(annual_gas_therms, 2),
    )
