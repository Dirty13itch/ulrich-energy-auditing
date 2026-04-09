from pathlib import Path
import subprocess
import sys


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
    content = output_path.read_text(encoding="utf-8")
    expected_content = (repo_root / "reports" / "sample-report.md").read_text(encoding="utf-8")

    assert content == expected_content
    assert "- Estimated annual opportunity: $1750" in content
    assert "- **Increase attic insulation** (high priority)" in content
    assert "- **Water heater replacement planning** (low priority)" in content
