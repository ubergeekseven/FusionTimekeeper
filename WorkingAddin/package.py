import os
import shutil
import json
from datetime import datetime

def create_release_package():
    # Create a temporary directory for packaging
    temp_dir = "temp_package"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    # Create the main add-in directory
    addin_dir = os.path.join(temp_dir, "CombineCut")
    os.makedirs(addin_dir)

    # Files to copy
    files_to_copy = [
        "CombineCut.py",
        "CombineCut.manifest",
        "AddInIcon.svg",
        "config.py",
        "README.md",
        "install.py",
        "install.bat"  # Include the batch installer
    ]

    # Directories to copy
    dirs_to_copy = [
        "commands",
        "lib"
    ]

    # Copy files
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, addin_dir)

    # Copy directories
    for dir_name in dirs_to_copy:
        if os.path.exists(dir_name):
            shutil.copytree(dir_name, os.path.join(addin_dir, dir_name))

    # Create the final zip file
    version = "1.0.0"  # This should match your manifest version
    timestamp = datetime.now().strftime("%Y%m%d")
    zip_name = f"CombineCut_v{version}_{timestamp}.zip"
    
    # Create the zip file
    shutil.make_archive(zip_name[:-4], 'zip', temp_dir)
    
    # Clean up
    shutil.rmtree(temp_dir)
    
    print(f"Created release package: {zip_name}")
    print("\nPackage structure:")
    print(f"CombineCut/")
    for file in files_to_copy:
        print(f"├── {file}")
    for dir_name in dirs_to_copy:
        print(f"├── {dir_name}/")
    print("└── ...")
    print("\nInstallation instructions:")
    print("Windows users:")
    print("1. Extract the ZIP file")
    print("2. Double-click install.bat")
    print("3. Follow the on-screen instructions")
    print("\nMac users:")
    print("1. Extract the ZIP file")
    print("2. Open Terminal and navigate to the extracted folder")
    print("3. Run: python3 install.py")
    print("4. Follow the on-screen instructions")

if __name__ == "__main__":
    create_release_package() 