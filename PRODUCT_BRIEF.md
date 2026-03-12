# Ulrich Energy Auditing MVP Brief

## Product

Ulrich Energy Auditing is a local audit-assistant product for producing consistent property energy audit summaries, upgrade recommendations, and follow-up talking points.

## Operator

- Primary operator: Shaun / Ulrich Energy Auditing
- Usage mode: solo local operator, later expandable to web/mobile intake

## Chosen MVP Workflow

1. Enter one building audit in a structured JSON file.
2. Run the CLI to analyze the audit.
3. Generate a Markdown report with:
   - energy use intensity summary
   - envelope and HVAC risk signals
   - recommended improvements
   - rough annual savings estimate
4. Review/edit the report before client delivery.

## Why This MVP

- It exits ambiguity without forcing a premature full-stack app.
- It captures the real core value: consistent audit interpretation and reporting.
- It is fast to run locally and easy to test.

## Data Model

- `building`
  - client name
  - address
  - building type
  - square footage
  - year built
- `systems`
  - HVAC age
  - water heater age
  - insulation R-value
  - blower door ACH50
  - duct leakage percent
- `consumption`
  - monthly electric usage
  - monthly gas therms
- `notes`
  - freeform operator notes

## Stack Decision

- Runtime: Python 3.11+
- Interface: local CLI
- Report format: Markdown
- Test path: `pytest`

## Local Scaffold Plan

- package source under `src/ulrich_energy_auditing`
- CLI entrypoint
- sample audit input
- generated report output path
- smoke tests for analysis and CLI output

## Acceptance Criteria

- can install in a clean venv
- can run the CLI against the sample audit file
- generates a readable report file
- `pytest` passes
- README and backlog match the actual workflow
