# AGENTS.md

## Repo Purpose

This repo is a small Python CLI for turning one audit JSON input into a Markdown recommendation report.

## Primary Files

- `README.md`
- `PRODUCT_BRIEF.md`
- `BACKLOG.md`
- `pyproject.toml`
- `src/ulrich_energy_auditing/cli.py`
- `src/ulrich_energy_auditing/analysis.py`
- `src/ulrich_energy_auditing/reporting.py`
- `examples/sample_audit.json`
- `tests/`

## Commands

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .[dev]
.\.venv\Scripts\python.exe -m ulrich_energy_auditing.cli examples\sample_audit.json --output reports\sample-report.md
.\.venv\Scripts\python.exe -m pytest
```

## Working Rules

- Keep the repo sample-only. Do not add real customer audit inputs or generated customer reports.
- Prefer small, explicit changes in `src/ulrich_energy_auditing/` over introducing extra framework layers.
- Preserve the current CLI-first workflow unless there is an explicit decision to expand scope.
- Keep tests runnable through plain `pytest`.
