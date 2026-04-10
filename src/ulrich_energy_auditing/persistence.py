from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from shutil import copyfile
from typing import Any

from ulrich_energy_auditing.importers import audit_to_payload
from ulrich_energy_auditing.models import AuditInput, AuditSummary

_DATA_ROOT_SEGMENTS = ("UlrichEnergyAuditing", "saved-audits")
_INDEX_FILE_NAME = "index.json"
_AUDITS_DIR_NAME = "audits"
_DEFAULT_HISTORY_LIMIT = 10


def save_audit_bundle(
    audit: AuditInput,
    summary: AuditSummary,
    *,
    report_markdown: str,
    input_path: Path,
    utility_bills_path: Path | None,
    save_name: str,
    pdf_output_path: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    timestamp = (now or datetime.now().astimezone()).replace(microsecond=0)
    data_root = get_saved_audits_root()
    audit_root = data_root / _AUDITS_DIR_NAME
    audit_root.mkdir(parents=True, exist_ok=True)

    slug_source = save_name.strip() or audit.building.client_name or audit.building.address
    save_id = _build_save_id(slug_source, audit_root, timestamp)
    bundle_root = audit_root / save_id
    bundle_root.mkdir(parents=True, exist_ok=False)

    audit_path = bundle_root / "audit.json"
    markdown_path = bundle_root / "report.md"
    pdf_path: Path | None = None
    metadata_path = bundle_root / "metadata.json"

    audit_path.write_text(json.dumps(audit_to_payload(audit), indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(report_markdown, encoding="utf-8")

    if pdf_output_path is not None:
        pdf_path = bundle_root / "report.pdf"
        copyfile(pdf_output_path, pdf_path)

    metadata = {
        "save_id": save_id,
        "saved_at": timestamp.isoformat(),
        "client_name": audit.building.client_name,
        "address": audit.building.address,
        "building_type": audit.building.building_type,
        "benchmark_pack_id": summary.benchmark_comparison.pack.pack_id,
        "input_source": _determine_input_source(input_path, utility_bills_path),
        "audit_json_path": str(audit_path),
        "markdown_report_path": str(markdown_path),
        "pdf_report_path": str(pdf_path) if pdf_path is not None else None,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    _write_index([metadata, *_read_index(data_root)], data_root)
    return metadata


def read_history(limit: int = _DEFAULT_HISTORY_LIMIT) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    return _read_index(get_saved_audits_root())[:limit]


def render_history(limit: int = _DEFAULT_HISTORY_LIMIT) -> str:
    data_root = get_saved_audits_root()
    records = read_history(limit=limit)
    if not records:
        return f"No saved audits found in {data_root}."

    lines = [f"Saved audits (showing {len(records)}):"]
    for record in records:
        lines.append(
            f"- {record['saved_at']} | {record['client_name']} | {record['building_type']} | "
            f"benchmark pack {record['benchmark_pack_id']}"
        )
        lines.append(f"  Save ID: {record['save_id']}")
        lines.append(f"  Audit JSON: {record['audit_json_path']}")
        lines.append(f"  Markdown report: {record['markdown_report_path']}")
        if record.get("pdf_report_path"):
            lines.append(f"  PDF report: {record['pdf_report_path']}")
    return "\n".join(lines)


def get_saved_audits_root() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    base_path = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
    return base_path.joinpath(*_DATA_ROOT_SEGMENTS)


def _build_save_id(slug_source: str, audit_root: Path, timestamp: datetime) -> str:
    base_id = f"{timestamp.strftime('%Y-%m-%d-%H%M%S')}-{_slugify(slug_source)}"
    candidate = base_id
    suffix = 2
    while (audit_root / candidate).exists():
        candidate = f"{base_id}-{suffix}"
        suffix += 1
    return candidate


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    normalized = normalized.strip("-")
    return normalized or "saved-audit"


def _determine_input_source(input_path: Path, utility_bills_path: Path | None) -> str:
    base = input_path.suffix.lower().lstrip(".") or "unknown"
    if utility_bills_path is None:
        return base
    return f"{base}+utility-bills"


def _read_index(data_root: Path) -> list[dict[str, Any]]:
    index_path = data_root / _INDEX_FILE_NAME
    if not index_path.exists():
        return []

    payload = json.loads(index_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Saved audit index at {index_path} must contain a top-level list.")
    return [entry for entry in payload if isinstance(entry, dict)]


def _write_index(records: list[dict[str, Any]], data_root: Path) -> None:
    data_root.mkdir(parents=True, exist_ok=True)
    index_path = data_root / _INDEX_FILE_NAME
    deduped: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for record in records:
        save_id = record.get("save_id")
        if not isinstance(save_id, str) or save_id in seen_ids:
            continue
        deduped.append(record)
        seen_ids.add(save_id)
    index_path.write_text(json.dumps(deduped, indent=2) + "\n", encoding="utf-8")
