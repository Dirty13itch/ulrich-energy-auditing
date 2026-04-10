from __future__ import annotations

import argparse
from pathlib import Path

from ulrich_energy_auditing.analysis import analyze_audit
from ulrich_energy_auditing.benchmark_packs import list_benchmark_packs
from ulrich_energy_auditing.importers import load_audit, write_audit_json
from ulrich_energy_auditing.persistence import render_history, save_audit_bundle
from ulrich_energy_auditing.reporting import render_markdown_report, write_pdf_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate an energy audit markdown report from JSON or CSV intake data."
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        help="Path to the audit JSON or audit CSV file.",
    )
    parser.add_argument(
        "--utility-bills",
        type=Path,
        help="Optional utility bill CSV used to derive annual electric and gas consumption totals.",
    )
    parser.add_argument(
        "--benchmark-pack",
        help="Optional benchmark pack ID override. Use --list-benchmark-packs to inspect the built-in pack catalog.",
    )
    parser.add_argument(
        "--list-benchmark-packs",
        action="store_true",
        help="Print the built-in benchmark pack catalog and exit.",
    )
    parser.add_argument(
        "--save-name",
        help="Optional label used to persist the normalized audit and generated reports into local history.",
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="Print saved audit history from the local operator data store and exit.",
    )
    parser.add_argument(
        "--history-limit",
        type=int,
        default=10,
        help="Maximum number of saved audit history entries to print when --history is used.",
    )
    parser.add_argument(
        "--emit-json",
        type=Path,
        help="Optional path to write the normalized audit payload as JSON before report generation.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports") / "audit-report.md",
        help="Path to the output markdown report.",
    )
    parser.add_argument(
        "--pdf-output",
        type=Path,
        help="Optional path to also write a PDF version of the report.",
    )
    args = parser.parse_args()

    if args.list_benchmark_packs:
        for pack in list_benchmark_packs():
            print(
                f"{pack.pack_id}: {pack.label} | region={pack.region} | "
                f"archetype={pack.building_archetype} | vintage={pack.vintage_label}"
            )
        return 0

    if args.history:
        print(render_history(limit=args.history_limit))
        return 0

    if args.input is None:
        parser.error("the following arguments are required: input")

    audit = load_audit(args.input, utility_bills_path=args.utility_bills)
    summary = analyze_audit(audit, benchmark_pack_id=args.benchmark_pack)
    report = render_markdown_report(audit, summary)
    if args.emit_json is not None:
        args.emit_json.parent.mkdir(parents=True, exist_ok=True)
        write_audit_json(audit, args.emit_json)
        print(f"Wrote normalized audit to {args.emit_json}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Wrote report to {args.output}")
    print(
        "Used benchmark pack "
        f"{summary.benchmark_comparison.pack.pack_id} "
        f"({summary.benchmark_comparison.pack.label})"
    )
    if args.pdf_output is not None:
        write_pdf_report(audit, summary, args.pdf_output)
        print(f"Wrote PDF report to {args.pdf_output}")
    if args.save_name is not None:
        metadata = save_audit_bundle(
            audit,
            summary,
            report_markdown=report,
            input_path=args.input,
            utility_bills_path=args.utility_bills,
            save_name=args.save_name,
            pdf_output_path=args.pdf_output,
        )
        saved_report_dir = Path(metadata["audit_json_path"]).parent
        print(f"Saved audit bundle {metadata['save_id']} to {saved_report_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
