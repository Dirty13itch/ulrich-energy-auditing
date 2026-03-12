from __future__ import annotations

import argparse
import json
from pathlib import Path

from ulrich_energy_auditing.analysis import analyze_audit
from ulrich_energy_auditing.models import AuditInput, BuildingProfile, BuildingSystems, ConsumptionProfile
from ulrich_energy_auditing.reporting import render_markdown_report


def _load_audit(path: Path) -> AuditInput:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return AuditInput(
        building=BuildingProfile(**payload["building"]),
        systems=BuildingSystems(**payload["systems"]),
        consumption=ConsumptionProfile(**payload["consumption"]),
        notes=payload.get("notes", []),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an energy audit markdown report.")
    parser.add_argument("input", type=Path, help="Path to the audit JSON file.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports") / "audit-report.md",
        help="Path to the output markdown report.",
    )
    args = parser.parse_args()

    audit = _load_audit(args.input)
    summary = analyze_audit(audit)
    report = render_markdown_report(audit, summary)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Wrote report to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
