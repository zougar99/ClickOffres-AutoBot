@echo off
setlocal
cd /d "%~dp0"

echo ================================================
echo   ClickOffres AutoBot - Build Release EXE
echo ================================================
echo.

set PYTHON_EXE=c:\Python314\python.exe
%PYTHON_EXE% --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found at %PYTHON_EXE%
    echo Edit build_release.bat and update PYTHON_EXE.
    pause
    exit /b 1
)

echo Installing build dependencies...
%PYTHON_EXE% -m pip install --upgrade pyinstaller
if %ERRORLEVEL% neq 0 (
    echo ERROR: Could not install pyinstaller.
    pause
    exit /b 1
)

echo.
echo Building executable...
%PYTHON_EXE% -m PyInstaller ^
  --noconfirm ^
  --onefile ^
  --windowed ^
  --name "ClickOffresAutoBot" ^
  --add-data "user_data.json;." ^
  --add-data "proxy_config.json;." ^
  --add-data "icon.ico;." ^
  --add-data "icon.png;." ^
  --hidden-import "customtkinter" ^
  --hidden-import "PIL" ^
  --collect-submodules "playwright" ^
  main_app.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Build failed.
    pause
    exit /b 1
)

echo.
echo Build complete: dist\ClickOffres.exe
echo NOTE: First run still requires Playwright Chromium installed.
echo Run once in terminal:
echo   %PYTHON_EXE% -m playwright install chromium
echo.
pause
