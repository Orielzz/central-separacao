@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto deps
py -3.12 -m venv .venv
if errorlevel 1 (
  echo Instale Python 3.12 pelo python.org, incluindo o Python Launcher.
  pause
  exit /b 1
)
:deps
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo A instalacao falhou. Verifique a conexao e as mensagens acima.
  pause
  exit /b 1
)
echo Instalacao concluida. Abra iniciar.bat.
pause
