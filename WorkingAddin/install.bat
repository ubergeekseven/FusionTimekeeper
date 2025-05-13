@echo off
setlocal enabledelayedexpansion

echo CombineCut Fusion 360 Add-in Installer
echo ======================================
echo.

:: Set the target directory
set "TARGET_DIR=%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\CombineCut"

:: Check if Fusion 360 is running
tasklist /FI "IMAGENAME eq Fusion360.exe" 2>NUL | find /I /N "Fusion360.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Warning: Fusion 360 is currently running.
    echo Please close Fusion 360 before continuing.
    echo.
    pause
    exit /b 1
)

:: Create the target directory if it doesn't exist
if not exist "%TARGET_DIR%" (
    mkdir "%TARGET_DIR%"
) else (
    echo Removing existing installation...
    rmdir /s /q "%TARGET_DIR%"
    mkdir "%TARGET_DIR%"
)

:: Create the exclude file for xcopy first
echo install.bat > install_exclude.txt
echo install.py >> install_exclude.txt
echo install_exclude.txt >> install_exclude.txt
echo *.zip >> install_exclude.txt
echo __pycache__ >> install_exclude.txt
echo .git >> install_exclude.txt
echo .vscode >> install_exclude.txt

:: Copy all files except those listed in install_exclude.txt
echo Installing to: %TARGET_DIR%
xcopy /E /I /Y /EXCLUDE:install_exclude.txt . "%TARGET_DIR%"

:: Clean up
del install_exclude.txt

echo.
echo Installation successful!
echo.
echo Next steps:
echo 1. Start Fusion 360
echo 2. Open the Add-Ins dialog (Press Shift+S)
echo 3. Enable the CombineCut add-in
echo.
pause
exit /b 0 