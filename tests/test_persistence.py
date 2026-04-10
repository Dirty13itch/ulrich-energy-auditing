import json
from datetime import datetime
from pathlib import Path

from ulrich_energy_auditing.analysis import analyze_audit
from ulrich_energy_auditing.importers import load_audit
from ulrich_energy_auditing.persistence import get_saved_audits_root, render_history, save_audit_bundle
from ulrich_energy_auditing.reporting import render_markdown_report


def test_save_audit_bundle_writes_index_and_bundle(monkeypatch, tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    local_app_data = tmp_path / "localappdata"
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))

    audit = load_audit(
        repo_root / "examples" / "sample_audit.csv",
        utility_bills_path=repo_root / "examples" / "sample_utility_bills.csv",
    )
    summary = analyze_audit(audit)
    report = render_markdown_report(audit, summary)

    pdf_output = tmp_path / "report.pdf"
    pdf_output.write_bytes(b"%PDF-test")

    metadata = save_audit_bundle(
        audit,
        summary,
        report_markdown=report,
        input_path=repo_root / "examples" / "sample_audit.csv",
        utility_bills_path=repo_root / "examples" / "sample_utility_bills.csv",
        save_name="Springfield sample",
        pdf_output_path=pdf_output,
        now=datetime.fromisoformat("2026-04-10T14:15:16-05:00"),
    )

    expected_root = local_app_data / "UlrichEnergyAuditing" / "saved-audits"
    assert get_saved_audits_root() == expected_root
    assert metadata["save_id"] == "2026-04-10-141516-springfield-sample"

    index_path = expected_root / "index.json"
    assert index_path.exists()
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert len(index_payload) == 1
    assert index_payload[0]["benchmark_pack_id"] == "mixed-humid-residential-legacy"

    audit_dir = expected_root / "audits" / metadata["save_id"]
    assert (audit_dir / "audit.json").exists()
    assert (audit_dir / "report.md").exists()
    assert (audit_dir / "report.pdf").exists()
    assert (audit_dir / "metadata.json").exists()


def test_render_history_reports_empty_store(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "localappdata"))

    history = render_history()

    assert "No saved audits found" in history

