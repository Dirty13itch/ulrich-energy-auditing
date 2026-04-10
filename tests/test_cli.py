import json
import os
from pathlib import Path
import subprocess
import sys

from pypdf import PdfReader


def test_cli_generates_report(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_path = tmp_path / "report.md"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ulrich_energy_auditing.cli",
            str(repo_root / "examples" / "sample_audit.json"),
            "--output",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert "Wrote report" in result.stdout
    assert "Used benchmark pack mixed-humid-residential-legacy" in result.stdout
    content = output_path.read_text(encoding="utf-8")
    assert "# Energy Audit Report" in content
    assert "Regional Benchmark" in content
    assert "Recommendations" in content


def test_cli_generates_report_from_csv_and_utility_bills(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_path = tmp_path / "report-from-csv.md"
    normalized_path = tmp_path / "normalized-audit.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ulrich_energy_auditing.cli",
            str(repo_root / "examples" / "sample_audit.csv"),
            "--utility-bills",
            str(repo_root / "examples" / "sample_utility_bills.csv"),
            "--emit-json",
            str(normalized_path),
            "--output",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert "Wrote normalized audit" in result.stdout
    assert "Wrote report" in result.stdout
    assert "Used benchmark pack mixed-humid-residential-legacy" in result.stdout
    assert normalized_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "# Energy Audit Report" in content
    assert "Benchmark pack: Mixed-Humid Residential Retrofit (Legacy Home)" in content
    assert "Estimated annual opportunity" in content


def test_cli_generates_pdf_report(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_path = tmp_path / "report.md"
    pdf_path = tmp_path / "report.pdf"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ulrich_energy_auditing.cli",
            str(repo_root / "examples" / "sample_audit.csv"),
            "--utility-bills",
            str(repo_root / "examples" / "sample_utility_bills.csv"),
            "--output",
            str(output_path),
            "--pdf-output",
            str(pdf_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert "Wrote PDF report" in result.stdout
    assert pdf_path.exists()
    reader = PdfReader(str(pdf_path))
    assert len(reader.pages) == 1
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "Energy Audit Report" in text
    assert "Ulrich Sample Residence" in text


def test_cli_lists_benchmark_packs_without_input() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ulrich_energy_auditing.cli",
            "--list-benchmark-packs",
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert "mixed-humid-residential-legacy" in result.stdout
    assert "hot-humid-small-office-legacy" in result.stdout


def test_cli_saves_audit_bundle_and_prints_history(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    local_app_data = tmp_path / "localappdata"
    env = dict(os.environ)
    env["LOCALAPPDATA"] = str(local_app_data)

    output_path = tmp_path / "saved-report.md"
    pdf_path = tmp_path / "saved-report.pdf"
    save_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ulrich_energy_auditing.cli",
            str(repo_root / "examples" / "sample_audit.csv"),
            "--utility-bills",
            str(repo_root / "examples" / "sample_utility_bills.csv"),
            "--output",
            str(output_path),
            "--pdf-output",
            str(pdf_path),
            "--save-name",
            "Operator Sample",
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=repo_root,
        env=env,
    )

    assert "Saved audit bundle 2026-" in save_result.stdout
    index_path = local_app_data / "UlrichEnergyAuditing" / "saved-audits" / "index.json"
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert len(index_payload) == 1
    assert index_payload[0]["input_source"] == "csv+utility-bills"

    history_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ulrich_energy_auditing.cli",
            "--history",
            "--history-limit",
            "5",
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=repo_root,
        env=env,
    )

    assert "Saved audits (showing 1)" in history_result.stdout
    assert "Ulrich Sample Residence" in history_result.stdout
    assert "benchmark pack mixed-humid-residential-legacy" in history_result.stdout
