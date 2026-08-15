@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [1/4] Creating Python environment...
  python -m venv .venv || goto :fail
)
echo [2/4] Installing dependencies...
.venv\Scripts\python.exe -m pip install -r requirements.txt || goto :fail
echo [3/4] Preparing AI models...
.venv\Scripts\python.exe ai\train_models.py || goto :fail
echo [4/4] Starting PulseGuard AI...
echo Open http://127.0.0.1:5000
.venv\Scripts\python.exe backend\app.py
goto :eof
:fail
echo.
echo PulseGuard could not start. Read the error above.
pause
