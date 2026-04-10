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

The intake path can now be reached either by:

- one canonical audit JSON file
- or a simpler audit CSV plus utility-bill CSV that normalize into the same audit model
- or a guided localhost browser wizard that writes the same normalized audit model

Delivery can now leave the CLI as:

- Markdown for operator editing
- PDF for client-ready handoff
- or a saved local audit bundle for later retrieval from history

The report layer now also adds regional benchmark context by selecting a built-in benchmark pack for the
building archetype and climate region. Operators can keep the auto-selected pack or override it explicitly
from the CLI when they want a different peer group.

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

## Intake Helpers

- audit CSV format: `section,field,value`
- utility bill CSV format: usage rows with `electric_kwh` and/or `gas_therms`
- import helpers normalize both paths into the same audit payload before analysis
- guided intake launches a local browser wizard from Python and still lands on that same normalized audit payload

## Benchmark Packs

- built-in benchmark packs cover legacy and modern residential plus small-office archetypes
- region handling currently supports mixed-humid, cold-climate, and hot-humid defaults
- the default pack is inferred from state abbreviation in the address, building type, and year built
- the operator can override the inferred pack with `--benchmark-pack`

## Stack Decision

- Runtime: Python 3.11+
- Interface: local CLI plus localhost browser wizard
- Report formats: Markdown and PDF
- persistence: local filesystem bundle store outside the repo
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
