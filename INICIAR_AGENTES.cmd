@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] No existe el entorno virtual .venv.
  echo Ejecuta primero INSTALAR_AGENTES.cmd
  pause
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\run_windows.ps1"
