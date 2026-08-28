@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] No existe .venv. Ejecuta INSTALAR_AGENTES.cmd primero.
  pause
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\run_windows.ps1"
