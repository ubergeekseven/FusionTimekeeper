import os
import sys
import shutil
import zipfile
from datetime import datetime

def create_package():
    """Create a zip package of the add-in."""
    try:
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Create the package name with version and date
        version = "1.0.0"  # This should match the version in the manifest
        date = datetime.now().strftime("%Y%m%d")
        package_name = f"FusionTimekeeper_v{version}_{date}"
        
        # Create the zip file
        zip_path = os.path.join(current_dir, f"{package_name}.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files to the zip
            for root, dirs, files in os.walk(current_dir):
                # Skip the .git directory and any other hidden directories
                if '.git' in root or any(d.startswith('.') for d in dirs):
                    continue
                
                for file in files:
                    # Skip the zip file itself and any other files we don't want to include
                    if file.endswith('.zip') or file.endswith('.pyc'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, current_dir)
                    zipf.write(file_path, arcname)
        
        print(f"Package created successfully: {zip_path}")
        return True

    except Exception as e:
        print(f"Error creating package: {str(e)}")
        return False

if __name__ == '__main__':
    if create_package():
        print("Packaging completed successfully!")
    else:
        print("Packaging failed!")
        sys.exit(1) 