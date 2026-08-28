$ErrorActionPreference='Stop'
Set-Location (Join-Path $PSScriptRoot '..')
$python='.\.venv\Scripts\python.exe'
if(-not (Test-Path $python)){throw 'No existe .venv. Ejecuta INSTALAR_AGENTES.cmd primero.'}
$env:APP_ENV = if($env:APP_ENV){$env:APP_ENV}else{'development'}
Write-Host 'HAGUER Agent Platform 2.0.0'
Write-Host 'Dashboard: http://127.0.0.1:8000/'
Write-Host 'Swagger:   http://127.0.0.1:8000/docs'
Write-Host 'API v1:    http://127.0.0.1:8000/api/v1/version'
Write-Host 'Detener:   Ctrl+C'
& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
