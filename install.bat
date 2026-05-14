@echo off
echo ================================================
echo   Click Offres - Installation
echo ================================================
echo.

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
    echo ERROR: Python not found.
    echo Install Python 3.10+ then re-run this installer.
    pause
    exit /b 1
)

echo.
echo Installing Python dependencies...
%PY_EXE% -m pip install customtkinter playwright Pillow
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: pip install failed!
    pause
    exit /b 1
)

echo.
echo Installing Chromium browser...
%PY_EXE% -m playwright install chromium
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Playwright install failed!
    pause
    exit /b 1
)

echo.
echo ================================================
echo   Installation complete!
echo   Double-click "run.bat" to start the app.
echo ================================================
pause
