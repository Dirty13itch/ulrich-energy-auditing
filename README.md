# Ulrich Energy Auditing

`ulrich-energy-auditing` is the seed product repo for Ulrich Energy Auditing. The MVP is a local Python audit workbench that turns one building-audit JSON file into a recommendation report with baseline intensity, upgrade priorities, and estimated annual savings.

## MVP Workflow

1. Capture one property audit in JSON.
2. Run the CLI against that audit file.
3. Review the generated Markdown report.
4. Use the report as the operator-ready summary for follow-up work and quoting.

## Canonical Local Workflow

```powershell
cd C:\Users\Shaun\dev\portfolio\ulrich-energy-auditing
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .[dev]
.\.venv\Scripts\python.exe -m ulrich_energy_auditing.cli examples\sample_audit.json --output reports\sample-report.md
```

## Smoke Path

```powershell
cd C:\Users\Shaun\dev\portfolio\ulrich-energy-auditing
.\smoke.ps1
```

`smoke.ps1` is the canonical proof lane for this repo. It bootstraps `.venv` on first run, refreshes the editable install when `pyproject.toml` changes, then runs the sample CLI path plus `pytest`. Use `.\smoke.ps1 -RefreshEnv` when you want to force a reinstall.

Recommendation and report behavior is intentionally locked to the sample contract in `examples/sample_audit.json` and `reports/sample-report.md`. If you change recommendation rules, rendered report wording, or savings assumptions, update the committed sample report and the matching tests in the same pass.

## Output Contract

- input: one audit JSON file
- output: one Markdown report
- operator: Shaun / Ulrich Energy Auditing
- posture: local-first CLI MVP

## Key Files

- `PRODUCT_BRIEF.md`: decision-complete product framing
- `BACKLOG.md`: next delivery steps after the MVP
- `examples/sample_audit.json`: runnable sample input
- `src/ulrich_energy_auditing/`: package source

## Status

- MVP scaffold exists and runs locally
- sample report generation is implemented
- next phase is richer intake, persistence, and export formats
