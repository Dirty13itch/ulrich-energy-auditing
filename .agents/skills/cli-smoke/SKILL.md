---
name: "cli-smoke"
description: "Use when working on ulrich-energy-auditing and the task changes CLI behavior, report generation, analysis logic, or any path that should be proven with the sample audit and pytest."
---


# Ulrich CLI Smoke

## Purpose

Verify the local CLI contract for `ulrich-energy-auditing` without drifting beyond the current sample-only MVP.

## Required workflow

From the repo root:

```powershell
.\smoke.ps1
```

Use `.\smoke.ps1 -RefreshEnv` when the task is explicitly about environment repair or dependency changes and you want to force the editable reinstall.

## Rules

- Do not introduce real customer data.
- Keep verification grounded in `examples/sample_audit.json`.
- Treat a generated sample report plus `pytest` as the minimum proof for behavior changes.
- Treat `smoke.ps1` as the canonical proof lane instead of retyping the bootstrap commands by hand.
- If the CLI output contract changes, update `README.md` and any relevant tests in the same pass.

## Output expectations

Report back with:

1. whether sample report generation passed
2. whether `pytest` passed
3. any output-path or contract changes
