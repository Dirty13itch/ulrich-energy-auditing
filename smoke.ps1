param(
    [string]$InputPath = "examples\sample_audit.json",
    [string]$OutputPath = "reports\sample-report.md",
    [switch]$RefreshEnv
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$installStamp = Join-Path $repoRoot ".venv\.codex-smoke-pyproject.sha256"
$pyprojectPath = Join-Path $repoRoot "pyproject.toml"

Push-Location $repoRoot

try {
    if (-not (Test-Path $python)) {
        python -m venv .venv
    }

    $currentHash = (Get-FileHash $pyprojectPath -Algorithm SHA256).Hash
    $previousHash = if (Test-Path $installStamp) {
        (Get-Content $installStamp -Raw).Trim()
    }
    else {
        ""
    }

    if ($RefreshEnv -or $currentHash -ne $previousHash) {
        & $python -m pip install -e .[dev]
        if ($LASTEXITCODE -ne 0) {
            throw "Editable install failed."
        }

        Set-Content -Path $installStamp -Value $currentHash -NoNewline
    }

    & $python -m ulrich_energy_auditing.cli $InputPath --output $OutputPath
    if ($LASTEXITCODE -ne 0) {
        throw "Sample report generation failed."
    }

    & $python -m pytest
    if ($LASTEXITCODE -ne 0) {
        throw "pytest failed."
    }

    Write-Host "Smoke passed."
}
finally {
    Pop-Location
}
