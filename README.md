# Ulrich Energy Auditing

`ulrich-energy-auditing` is the seed product repo for Ulrich Energy Auditing. The MVP is a local Python audit workbench that turns one building-audit JSON file into a recommendation report with baseline intensity, upgrade priorities, and estimated annual savings.

## MVP Workflow

1. Capture one property audit in JSON.
2. Run the CLI against that audit file.
3. Review the generated Markdown report.
4. Use the report as the operator-ready summary for follow-up work and quoting.

The CLI also now supports a simpler CSV-first intake path:

1. Capture the building and system fields in `examples/sample_audit.csv` format.
2. Drop monthly electric and gas usage into `examples/sample_utility_bills.csv` format.
3. Run one command to normalize the intake into audit JSON and generate the report.

## Canonical Local Workflow

```powershell
cd C:\Users\Shaun\dev\portfolio\ulrich-energy-auditing
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .[dev]
.\.venv\Scripts\python.exe -m ulrich_energy_auditing.cli examples\sample_audit.json --output reports\sample-report.md
```

CSV + utility-bill helper path:

```powershell
cd C:\Users\Shaun\dev\portfolio\ulrich-energy-auditing
.\.venv\Scripts\python.exe -m ulrich_energy_auditing.cli examples\sample_audit.csv --utility-bills examples\sample_utility_bills.csv --emit-json reports\sample-audit-from-csv.json --output reports\sample-report-from-csv.md
```

PDF export path:

```powershell
cd C:\Users\Shaun\dev\portfolio\ulrich-energy-auditing
.\.venv\Scripts\python.exe -m ulrich_energy_auditing.cli examples\sample_audit.csv --utility-bills examples\sample_utility_bills.csv --output reports\sample-report-from-csv.md --pdf-output reports\sample-report-from-csv.pdf
```

Benchmark-pack catalog:

```powershell
cd C:\Users\Shaun\dev\portfolio\ulrich-energy-auditing
.\.venv\Scripts\python.exe -m ulrich_energy_auditing.cli --list-benchmark-packs
```

Explicit benchmark-pack override:

```powershell
cd C:\Users\Shaun\dev\portfolio\ulrich-energy-auditing
.\.venv\Scripts\python.exe -m ulrich_energy_auditing.cli examples\sample_audit.json --benchmark-pack mixed-humid-residential-legacy --output reports\sample-report.md
```

## Smoke Path

```powershell
cd C:\Users\Shaun\dev\portfolio\ulrich-energy-auditing
.\smoke.ps1
```

`smoke.ps1` is the canonical proof lane for this repo. It bootstraps `.venv` on first run, refreshes the editable install when `pyproject.toml` changes, then runs the sample CLI path plus `pytest`. Use `.\smoke.ps1 -RefreshEnv` when you want to force a reinstall.

## Output Contract

- input: one audit JSON file
- alternate intake: one audit CSV plus optional utility-bill CSV overlay
- benchmark context: one built-in regional/archetype benchmark pack, auto-selected or overridden by CLI
- primary delivery: one Markdown report
- optional delivery: one concise PDF handoff from the same report contract
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
- CSV and utility-bill import helpers are implemented
- PDF export is implemented
- benchmark packs for regional building archetypes are implemented
- next phase is persistence, saved audit history, and richer delivery outputs
