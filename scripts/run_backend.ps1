# Run SolanaTxPlain backend (API only). From project root: .\scripts\run_backend.ps1
Set-Location $PSScriptRoot\..
if (Test-Path .\.venv\Scripts\Activate.ps1) {
    .\.venv\Scripts\Activate.ps1
}
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
