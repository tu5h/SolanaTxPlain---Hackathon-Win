# Run SolanaTxPlain frontend (static server on port 3000). From project root: .\scripts\run_frontend.ps1
Set-Location $PSScriptRoot\..
python -m http.server 3000 --directory frontend
