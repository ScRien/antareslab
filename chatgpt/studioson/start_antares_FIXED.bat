@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

set "VENV_DIR=antares_env"
set "REQ_FILE=requirements.txt"
set "APP_PRIMARY=antares_studio_final.py"
set "APP_FALLBACK=antares_main_improved.py"

echo ===============================================================
echo  ANTARES - Studio Launcher (Windows)
echo ===============================================================
echo.

REM Find Python launcher
set "PY_CMD="
where py >nul 2>&1
if %errorlevel%==0 set "PY_CMD=py -3"

if "%PY_CMD%"=="" (
  where python >nul 2>&1
  if %errorlevel%==0 set "PY_CMD=python"
)

if "%PY_CMD%"=="" (
  echo [ERROR] Python not found.
  echo Install Python 3.8+ and re-run this file.
  pause
  exit /b 1
)

REM Create venv if missing
if not exist "%VENV_DIR%\Scripts\python.exe" (
  echo [*] Creating virtual environment: %VENV_DIR%
  %PY_CMD% -m venv "%VENV_DIR%"
  if not %errorlevel%==0 (
    echo [ERROR] Failed to create venv.
    pause
    exit /b 1
  )
)

REM Activate venv
call "%VENV_DIR%\Scripts\activate.bat"
if not %errorlevel%==0 (
  echo [ERROR] Failed to activate venv.
  pause
  exit /b 1
)

REM Upgrade pip toolchain (best effort)
python -m pip install --upgrade pip setuptools wheel >nul 2>&1

REM Install requirements if present
if exist "%REQ_FILE%" (
  echo [*] Installing requirements from %REQ_FILE%
  pip install -r "%REQ_FILE%"
  if not %errorlevel%==0 (
    echo [ERROR] pip install failed.
    echo Try manually: pip install -r "%REQ_FILE%"
    pause
    exit /b 1
  )
) else (
  echo [WARN] requirements.txt not found. Skipping dependency install.
)

echo.
echo [*] Starting application...
echo.

if exist "%APP_PRIMARY%" (
  python "%APP_PRIMARY%"
) else if exist "%APP_FALLBACK%" (
  python "%APP_FALLBACK%"
) else (
  echo [ERROR] App file not found.
  echo Expected: %APP_PRIMARY%  (or %APP_FALLBACK%)
  echo.
  dir
  pause
  exit /b 1
)

set "EXITCODE=%errorlevel%"
if not "%EXITCODE%"=="0" (
  echo.
  echo [ERROR] App exited with code %EXITCODE%
  pause
)

endlocal
exit /b %EXITCODE%
