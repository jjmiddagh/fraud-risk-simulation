# setup.ps1
$ErrorActionPreference = "Stop"
$proj = Split-Path -Leaf (Get-Location)
Write-Host "==> Setting up $proj" -ForegroundColor Cyan

# Ensure Python exists
$py = Join-Path ".\.venv\Scripts" "python.exe"
if (-not (Test-Path $py)) {
  Write-Host "==> Creating venv .venv" -ForegroundColor Cyan
  python -m venv .venv
  $py = Join-Path ".\.venv\Scripts" "python.exe"
}

# Use venv's python for everything
& $py -m pip --version | Write-Host
Write-Host "==> Upgrading pip/setuptools/wheel" -ForegroundColor Cyan
& $py -m pip install --upgrade pip setuptools wheel

Write-Host "==> Installing requirements" -ForegroundColor Cyan
& $py -m pip install -r requirements.txt

Write-Host "==> Running demo simulation" -ForegroundColor Cyan
& $py run_simulation.py

Write-Host "==> Done. Artifacts in .\outputs" -ForegroundColor Green
