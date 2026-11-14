@echo off
cd /d "%~dp0"
py -3 -m pip install -r requirements.txt
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name ForeverGoldCompanion desktop.py
echo EXE created in dist\ForeverGoldCompanion.exe
pause
