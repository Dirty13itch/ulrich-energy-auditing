param(
    [string]$InputPath = "examples\sample_audit.json",
    [string]$OutputPath = "reports\sample-report.md",
    [string]$CsvInputPath = "examples\sample_audit.csv",
    [string]$UtilityBillsPath = "examples\sample_utility_bills.csv",
    [string]$CsvOutputPath = "reports\sample-report-from-csv.md",
    [string]$NormalizedAuditPath = "reports\sample-audit-from-csv.json",
    [string]$PdfOutputPath = "reports\sample-report-from-csv.pdf",
    [switch]$RefreshEnv
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$installStamp = Join-Path $repoRoot ".venv\.codex-smoke-pyproject.sha256"
$pyprojectPath = Join-Path $repoRoot "pyproject.toml"
$smokeLocalAppData = Join-Path $env:TEMP "ulrich-energy-auditing-smoke-localappdata"
$originalLocalAppData = $env:LOCALAPPDATA

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

    if (Test-Path $smokeLocalAppData) {
        Remove-Item -LiteralPath $smokeLocalAppData -Recurse -Force
    }
    New-Item -ItemType Directory -Path $smokeLocalAppData | Out-Null
    $env:LOCALAPPDATA = $smokeLocalAppData

    & $python -m ulrich_energy_auditing.cli $InputPath --output $OutputPath
    if ($LASTEXITCODE -ne 0) {
        throw "Sample report generation failed."
    }

    & $python -m ulrich_energy_auditing.cli $CsvInputPath --utility-bills $UtilityBillsPath --emit-json $NormalizedAuditPath --output $CsvOutputPath --pdf-output $PdfOutputPath --save-name "Smoke sample audit"
    if ($LASTEXITCODE -ne 0) {
        throw "CSV import report generation failed."
    }

    & $python -m ulrich_energy_auditing.cli --history --history-limit 5
    if ($LASTEXITCODE -ne 0) {
        throw "Audit history listing failed."
    }

    & $python -m pytest
    if ($LASTEXITCODE -ne 0) {
        throw "pytest failed."
    }

    Write-Host "Smoke passed."
}
finally {
    if ($null -eq $originalLocalAppData) {
        Remove-Item Env:LOCALAPPDATA -ErrorAction SilentlyContinue
    }
    else {
        $env:LOCALAPPDATA = $originalLocalAppData
    }
    if (Test-Path $smokeLocalAppData) {
        Remove-Item -LiteralPath $smokeLocalAppData -Recurse -Force
    }
    Pop-Location
}
