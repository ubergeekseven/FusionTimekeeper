import os
import sys
import shutil
import zipfile
from datetime import datetime

def create_distribution_package():
    """Create a distribution package with all necessary files and install script."""
    try:
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Create version and date information
        version = "1.0.0"  # Should match the version in the manifest
        date = datetime.now().strftime("%Y%m%d")
        package_name = f"FusionTimekeeper_v{version}_{date}"
        
        # Create the distribution directory
        dist_dir = os.path.join(current_dir, "dist")
        if os.path.exists(dist_dir):
            shutil.rmtree(dist_dir)
        os.makedirs(dist_dir)
        
        # Create package directory inside dist
        package_dir = os.path.join(dist_dir, package_name)
        os.makedirs(package_dir)
        
        # Files and directories to exclude from the package
        exclude = [
            '.git', 
            '.vscode', 
            '__pycache__', 
            'dist',
            '.cursor',
            '.gitignore',
            '*.zip',
            '*.pyc',
            'package.py'
        ]
        
        # Copy all necessary files to the package directory
        for item in os.listdir(current_dir):
            # Skip excluded items
            skip = False
            for pattern in exclude:
                if pattern.startswith('*'):
                    if item.endswith(pattern[1:]):
                        skip = True
                        break
                elif item == pattern:
                    skip = True
                    break
            
            if skip:
                continue
                
            source = os.path.join(current_dir, item)
            dest = os.path.join(package_dir, item)
            
            if os.path.isdir(source):
                shutil.copytree(source, dest, ignore=shutil.ignore_patterns(*exclude))
            else:
                shutil.copy2(source, dest)
        
        # Create the install scripts
        create_install_batch_file(package_dir)
        create_install_shell_script(package_dir)
        
        # Create a zip file of the package
        zip_path = os.path.join(dist_dir, f"{package_name}.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, dist_dir)
                    zipf.write(file_path, arcname)
        
        print(f"Distribution package created successfully: {zip_path}")
        print(f"Unpacked files available at: {package_dir}")
        return True

    except Exception as e:
        print(f"Error creating distribution package: {str(e)}")
        traceback.print_exc()
        return False

def create_install_batch_file(package_dir):
    """Create the install.bat file in the package directory."""
    install_bat_content = """@echo off
setlocal enabledelayedexpansion

echo FusionTimekeeper Add-in Installer
echo ===============================
echo.

:: Set the target directory
set "TARGET_DIR=%APPDATA%\\Autodesk\\Autodesk Fusion 360\\API\\AddIns\\FusionTimekeeper"

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

:: Get the script directory (where the install.bat is located)
set "SCRIPT_DIR=%~dp0"

:: Files to exclude from the installation
set "EXCLUDE_FILES=install.bat install.sh"

:: Copy only the add-in files to the target directory
echo Installing to: %TARGET_DIR%
for %%F in ("%SCRIPT_DIR%*.*") do (
    set "FILE_NAME=%%~nxF"
    if "!EXCLUDE_FILES:%%~nxF=!" == "!EXCLUDE_FILES!" (
        copy "%%F" "%TARGET_DIR%\\" > nul
    )
)

:: Copy all subdirectories except those we want to exclude
for /d %%D in ("%SCRIPT_DIR%*") do (
    set "DIR_NAME=%%~nxD"
    if "!DIR_NAME!" NEQ "dist" if "!DIR_NAME!" NEQ ".git" if "!DIR_NAME!" NEQ ".vscode" if "!DIR_NAME!" NEQ "__pycache__" if "!DIR_NAME!" NEQ ".cursor" (
        xcopy "%%D" "%TARGET_DIR%\\%%~nxD\\" /E /I /Y > nul
    )
)

echo.
echo Installation successful!
echo.
echo Next steps:
echo 1. Start Fusion 360
echo 2. Open the Add-Ins dialog (Press Shift+S)
echo 3. Enable the FusionTimekeeper add-in
echo.
pause
exit /b 0
"""

    with open(os.path.join(package_dir, "install.bat"), "w", newline="\r\n") as f:
        f.write(install_bat_content)

def create_install_shell_script(package_dir):
    """Create the install.sh file in the package directory for Mac users."""
    install_sh_content = """#!/bin/bash

echo "FusionTimekeeper Add-in Installer"
echo "==============================="
echo

# Set the target directory
TARGET_DIR="$HOME/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/FusionTimekeeper"

# Check if Fusion 360 is running
if pgrep -x "Fusion360" > /dev/null; then
    echo "Warning: Fusion 360 is currently running."
    echo "Please close Fusion 360 before continuing."
    echo
    read -p "Press Enter to continue..."
    exit 1
fi

# Create the target directory if it doesn't exist
if [ ! -d "$TARGET_DIR" ]; then
    mkdir -p "$TARGET_DIR"
else
    echo "Removing existing installation..."
    rm -rf "$TARGET_DIR"
    mkdir -p "$TARGET_DIR"
fi

# Get the script directory (where the install.sh is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Files to exclude from the installation
EXCLUDE_FILES="install.bat install.sh"

# Copy only the add-in files to the target directory
echo "Installing to: $TARGET_DIR"

# Copy files
find "$SCRIPT_DIR" -maxdepth 1 -type f | while read file; do
    filename=$(basename "$file")
    if [[ ! "$EXCLUDE_FILES" =~ "$filename" ]]; then
        cp "$file" "$TARGET_DIR/"
    fi
done

# Copy directories (excluding specific ones)
find "$SCRIPT_DIR" -maxdepth 1 -type d | grep -v "^$SCRIPT_DIR$" | while read dir; do
    dirname=$(basename "$dir")
    if [[ "$dirname" != ".git" && "$dirname" != ".vscode" && "$dirname" != "__pycache__" && "$dirname" != "dist" && "$dirname" != ".cursor" ]]; then
        cp -R "$dir" "$TARGET_DIR/"
    fi
done

echo
echo "Installation successful!"
echo
echo "Next steps:"
echo "1. Start Fusion 360"
echo "2. Open the Add-Ins dialog (Press Shift+S)"
echo "3. Enable the FusionTimekeeper add-in"
echo
read -p "Press Enter to continue..."
exit 0
"""

    with open(os.path.join(package_dir, "install.sh"), "w", newline="\n") as f:
        f.write(install_sh_content)
    
    # Make the shell script executable on Unix-like systems
    try:
        if sys.platform != "win32":
            os.chmod(os.path.join(package_dir, "install.sh"), 0o755)
    except Exception as e:
        print(f"Warning: Could not set executable permissions on install.sh: {str(e)}")

if __name__ == '__main__':
    import traceback
    try:
        if create_distribution_package():
            print("Packaging completed successfully!")
        else:
            print("Packaging failed!")
            sys.exit(1)
    except Exception as e:
        print(f"Unhandled error: {str(e)}")
        traceback.print_exc()
        sys.exit(1) 