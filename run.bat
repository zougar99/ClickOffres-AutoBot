@echo off
cd /d "%~dp0"
echo Starting ClickOffres AutoBot...
set PY_EXE=

if exist "c:\Python314\python.exe" set PY_EXE=c:\Python314\python.exe
if "%PY_EXE%"=="" (
    py -3 --version >nul 2>&1
    if %ERRORLEVEL%==0 set PY_EXE=py -3
)
if "%PY_EXE%"=="" (
    python --version >nul 2>&1
    if %ERRORLEVEL%==0 set PY_EXE=python
)

if "%PY_EXE%"=="" (
    echo.
    echo ERROR: Python not found.
    echo - Install Python 3.10+ OR
    echo - Update run.bat with your python path.
    pause
    exit /b 1
)

%PY_EXE% main_app.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Application crashed! Check the error above.
    echo If modules are missing, run install.bat first.
    pause
)
