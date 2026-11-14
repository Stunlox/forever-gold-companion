@echo off
setlocal
cd /d "%~dp0"
py -3 -m pip install --upgrade pyinstaller requests
if errorlevel 1 goto fail
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name ForeverProfessionOptimizer --collect-all certifi desktop.py
if errorlevel 1 goto fail
echo.
echo Your executable is in dist\ForeverProfessionOptimizer.exe
pause
exit /b 0
:fail
echo Build failed. Ensure Python 3.10+ is installed on Windows with the py launcher.
pause
exit /b 1
