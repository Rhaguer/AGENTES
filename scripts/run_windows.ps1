$ErrorActionPreference='Stop'
Set-Location (Join-Path $PSScriptRoot '..')
$python='.\.venv\Scripts\python.exe'
if(-not (Test-Path $python)){throw 'No existe .venv. Ejecuta INSTALAR_AGENTES.cmd primero.'}
Write-Host 'Dashboard: http://127.0.0.1:8000/'
Write-Host 'Swagger:   http://127.0.0.1:8000/docs'
Write-Host 'Detener:   Ctrl+C'
& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
