$ErrorActionPreference='Stop'
Set-Location (Join-Path $PSScriptRoot '..')
Write-Host '=== HAGUER AGENT PLATFORM 2.0.0 - REPARACION FORZADA ==='
$pythonCmd=Get-Command python -ErrorAction SilentlyContinue
if(-not $pythonCmd){throw 'Python no está disponible en PATH.'}
$python=$pythonCmd.Source
if(Test-Path '.\.venv'){Remove-Item '.\.venv' -Recurse -Force}
& $python -m venv '.\.venv'
$venvPython=(Resolve-Path '.\.venv\Scripts\python.exe').Path
& $venvPython -m pip install --upgrade pip setuptools wheel
& $venvPython -m pip install -r '.\requirements.txt'
if(-not (Test-Path '.\.env')){Copy-Item '.\.env.example' '.\.env'}
& $venvPython -m compileall -q '.\app'
$env:APP_ENV='testing'; & $venvPython -m pytest -q; & $venvPython '.\scripts\selftest.py'; Remove-Item Env:APP_ENV -ErrorAction SilentlyContinue
Write-Host 'REPARACION OK. Iniciando...'
& $venvPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000
