import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path

def get_fusion_addins_path():
    system = platform.system().lower()
    if system == "windows":
        # Windows path
        return os.path.join(os.environ['APPDATA'], 'Autodesk', 'Autodesk Fusion 360', 'API', 'AddIns')
    elif system == "darwin":
        # Mac path
        return os.path.expanduser('~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns')
    else:
        raise SystemError(f"Unsupported operating system: {system}")

def install_addin():
    try:
        # Get the current directory (where the installer is running from)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Get the Fusion 360 AddIns directory
        fusion_addins_path = get_fusion_addins_path()
        target_dir = os.path.join(fusion_addins_path, "CombineCut")
        
        # Create the AddIns directory if it doesn't exist
        os.makedirs(fusion_addins_path, exist_ok=True)
        
        # Remove existing installation if it exists
        if os.path.exists(target_dir):
            print("Removing existing installation...")
            shutil.rmtree(target_dir)
        
        # Copy all files to the target directory
        print(f"Installing to: {target_dir}")
        shutil.copytree(current_dir, target_dir, 
                       ignore=shutil.ignore_patterns('*.pyc', 'temp_*', '__pycache__', '*.zip', 'install.py'))
        
        print("\nInstallation successful!")
        print("\nNext steps:")
        print("1. Restart Fusion 360 if it's running")
        print("2. Open the Add-Ins dialog (Press Shift+S)")
        print("3. Enable the CombineCut add-in")
        
        # Keep the window open on Windows
        if platform.system().lower() == "windows":
            input("\nPress Enter to exit...")
            
    except Exception as e:
        print(f"\nError during installation: {str(e)}")
        print("\nPlease try the manual installation method described in the README.md file.")
        if platform.system().lower() == "windows":
            input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    install_addin() 