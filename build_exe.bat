@echo off
cd /d "%~dp0"
python -m pip install "pyinstaller>=6,<7"
if errorlevel 1 goto error
python -m PyInstaller --noconfirm --clean --windowed --contents-directory "." --name "TiebaPet" --add-data "assets;assets" --add-data "data;data" --add-data "extensions;extensions" main.py
if errorlevel 1 goto error
echo.
echo Build completed: dist\TiebaPet\TiebaPet.exe
pause
exit /b 0

:error
echo.
echo Build failed. Check the messages above.
pause
exit /b 1
