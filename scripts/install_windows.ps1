$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..
if (-not (Test-Path .venv)) { py -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
Write-Host 'Instalación completada.'
Write-Host 'Edita .env y configura MS_CLIENT_ID / Google credentials / GitHub token.'
