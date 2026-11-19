@echo off
setlocal
cd /d "%~dp0"
echo ==============================================
echo Saudi Legal AI - Windows Desktop Build
echo ==============================================
where py >nul 2>nul
if errorlevel 1 (
  echo Python 3 launcher was not found. Install Python 3.11+ first.
  start https://www.python.org/downloads/windows/
  pause
  exit /b 1
)
where ISCC >nul 2>nul
if errorlevel 1 (
  echo Inno Setup 6 compiler (ISCC.exe) was not found.
  echo Install Inno Setup 6, then run this file again.
  start https://jrsoftware.org/isinfo.php
  pause
  exit /b 1
)
if not exist ".build-venv\Scripts\python.exe" py -3 -m venv .build-venv
if errorlevel 1 goto error
call .build-venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 goto error
echo Building standalone desktop application...
pyinstaller --noconfirm packaging\SaudiLegalAI.spec
if errorlevel 1 goto error
echo Building Windows installer...
ISCC packaging\SaudiLegalAI.iss
if errorlevel 1 goto error
echo.
echo SUCCESS:
echo dist-installer\SaudiLegalAI-Setup-Windows.exe
echo.
echo Install this file to add the desktop shortcut.
pause
exit /b 0
:error
echo.
echo BUILD FAILED. Copy the full error output for troubleshooting.
pause
exit /b 1
