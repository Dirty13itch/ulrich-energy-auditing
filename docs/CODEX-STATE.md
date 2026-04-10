# CODEX-STATE

Last updated: 2026-04-10

## Purpose

This repo is a local-first Python CLI that turns one audit JSON input into one Markdown recommendation report.
It should stay sample-only and CLI-first unless scope is explicitly expanded.

## Start Here

1. Read `AGENTS.md`.
2. Read `README.md`.
3. Read `PRODUCT_BRIEF.md` for scope boundaries.
4. Read `BACKLOG.md` if the task is roadmap or expansion oriented.

## Current Working Assumptions

- No real customer data should enter this repo.
- The current contract is one JSON input to one Markdown report.
- Intake can now start from audit CSV plus utility-bill CSV as long as both normalize into the same audit payload.
- The CLI can also emit a PDF handoff from the same report sections when `--pdf-output` is provided.
- The CLI now adds a regional benchmark pack automatically and can override that pack explicitly with `--benchmark-pack`.
- The CLI can persist saved audits and report history outside the repo in `%LOCALAPPDATA%\UlrichEnergyAuditing\saved-audits`.
- Small explicit edits in `src/ulrich_energy_auditing/` are preferred over framework growth.
- The main checkout should be kept clean between tranches.

## PR Follow-Through

- PR `#1` (`chore: harden cli smoke lane`) is still open and still a draft.
- GitHub currently reports the branch as mergeable, but there are no human reviews and one required signal is red.
- The failing signal is the external `Vercel` status, not the repo proof lane.
- The linked Vercel project is configured as `nextjs`, so it runs `next build` against this Python CLI repo and fails with `No Next.js version detected`.
- In-repo proof is still `.\smoke.ps1`; keep using that for repo truth.
- Recommended disposition as of 2026-04-08: stay parked until the Vercel integration is removed, ignored, or reconfigured outside this repo.

## Fast Verification Paths

```powershell
.\smoke.ps1
```

`smoke.ps1` is the repo proof command. It creates `.venv` if missing, only refreshes the editable install when `pyproject.toml` changes, and then runs both the sample report generation path and `pytest`. Use `.\smoke.ps1 -RefreshEnv` to force a reinstall when environment repair is the point of the check.

The smoke path now verifies both:

- the original sample JSON intake
- the CSV plus utility-bill normalization path
- PDF report generation from the normalized audit
- benchmark-pack catalog and regional benchmark content through pytest coverage
- saved audit bundle creation and local history listing through a temp `%LOCALAPPDATA%` override

## PR Follow-Through

- PR `#1` (`chore: harden cli smoke lane`) is still open as a draft.
- Local repo proof remains green via `.\smoke.ps1`.
- The only failing GitHub status is `Vercel`, and the failure is external to this repo's Python CLI contract: the connected Vercel project is configured to run `next build`, then errors because this repo has no `package.json` or `next` dependency.
- There are no human review requests or requested changes on the PR right now.
- Current disposition: keep the PR parked until the Vercel integration is disconnected, reconfigured away from `nextjs`, or made non-blocking for this repository.

## Current Codex Gaps

- Only one repo-local skill exists so far: `.agents/skills/cli-smoke/SKILL.md`
- No repo-local `.codex/config.toml`
- Next product tranche is a guided intake UI once the CLI schema stabilizes.

Best next repo-local Codex upgrade after this file: add a repo-local `.codex/config.toml` only if this repo develops workflow-specific defaults.
