$ErrorActionPreference='Stop'
Set-Location (Join-Path $PSScriptRoot '..')
Write-Host '=== HAGUER AGENT PLATFORM 2.0.0 - INSTALACION ==='
$pythonCmd=Get-Command python -ErrorAction SilentlyContinue
if(-not $pythonCmd){throw 'Python no está disponible en PATH. Instala Python 3.11+.'}
$python=$pythonCmd.Source
& $python --version
if(Test-Path '.\.venv'){Write-Host 'Usando .venv existente.'}else{& $python -m venv '.\.venv'}
$venvPython=(Resolve-Path '.\.venv\Scripts\python.exe').Path
& $venvPython -m ensurepip --upgrade
& $venvPython -m pip install --upgrade pip setuptools wheel
& $venvPython -m pip install -r '.\requirements.txt'
if(-not (Test-Path '.\.env')){Copy-Item '.\.env.example' '.\.env'}
& $venvPython -m compileall -q '.\app' '.\scripts' '.\tests'
$env:APP_ENV='testing'
& $venvPython -m pytest -q
& $venvPython '.\scripts\selftest.py'
Remove-Item Env:APP_ENV -ErrorAction SilentlyContinue
Write-Host 'INSTALACION Y VALIDACION OK'
Write-Host 'Ejecuta INICIAR_AGENTES.cmd'
