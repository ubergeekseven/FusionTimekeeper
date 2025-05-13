@echo off
echo Installing Fusion Timekeeper Add-in...
python install.py
if errorlevel 1 (
    echo Installation failed!
    pause
    exit /b 1
)
echo Installation completed successfully!
pause 