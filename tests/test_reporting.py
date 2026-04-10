from pathlib import Path

from pypdf import PdfReader

from ulrich_energy_auditing.analysis import analyze_audit
from ulrich_energy_auditing.importers import load_audit
from ulrich_energy_auditing.reporting import write_pdf_report


def test_write_pdf_report_creates_readable_document(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    audit = load_audit(
        repo_root / "examples" / "sample_audit.csv",
        utility_bills_path=repo_root / "examples" / "sample_utility_bills.csv",
    )
    summary = analyze_audit(audit)
    pdf_path = tmp_path / "energy-audit.pdf"

    write_pdf_report(audit, summary, pdf_path)

    assert pdf_path.exists()
    reader = PdfReader(str(pdf_path))
    assert len(reader.pages) == 1
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "Regional Benchmark" in text
    assert "Systems Snapshot" in text
    assert "Recommendations" in text
