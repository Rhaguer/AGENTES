$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

Write-Host '=== HAGUER AGENT PLATFORM - INSTALACION FORZADA ==='

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    throw 'Python no está disponible en PATH. Instala Python 3.11+ y marca Add python.exe to PATH.'
}
$python = $pythonCmd.Source
Write-Host "Python: $python"
& $python --version

if (-not (Test-Path '.\requirements.txt')) {
    throw 'No existe requirements.txt. Verifica que estés usando la carpeta correcta del proyecto.'
}
if (-not (Test-Path '.\app\main.py')) {
    throw 'No existe app\main.py. Verifica que el ZIP se haya extraído completo.'
}

if (Test-Path '.\.venv') {
    Write-Host 'Eliminando entorno virtual anterior...'
    Remove-Item '.\.venv' -Recurse -Force
}

Write-Host 'Creando .venv...'
& $python -m venv '.\.venv'
$venvPython = (Resolve-Path '.\.venv\Scripts\python.exe').Path
if (-not (Test-Path $venvPython)) {
    throw 'No se creó .venv\Scripts\python.exe.'
}

Write-Host "Python virtual: $venvPython"
& $venvPython -m ensurepip --upgrade
& $venvPython -m pip install --upgrade pip setuptools wheel
& $venvPython -m pip install -r '.\requirements.txt'

if (-not (Test-Path '.\.env')) {
    Copy-Item '.\.env.example' '.\.env' -Force
}

Write-Host 'Validando imports...'
& $venvPython -c "import app.main; print('IMPORT APP OK')"

if (Test-Path '.\scripts\selftest.py') {
    Write-Host 'Ejecutando self-test...'
    & $venvPython '.\scripts\selftest.py'
}

Write-Host 'Iniciando API en http://127.0.0.1:8000 ...'
& $venvPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000
