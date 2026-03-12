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
    assert "# Energy Audit Report" in content
    assert "Recommendations" in content
