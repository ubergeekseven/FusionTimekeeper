import os
import sys
import shutil
import platform

def get_addin_path():
    """Get the path to the Fusion 360 add-ins directory."""
    if platform.system() == 'Windows':
        return os.path.join(os.getenv('APPDATA'), 'Autodesk', 'Autodesk Fusion 360', 'API', 'AddIns')
    else:  # macOS
        return os.path.expanduser('~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns')

def install_addin():
    """Install the add-in to Fusion 360's add-ins directory."""
    try:
        # Get the current directory (where this script is located)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Get the add-in name from the manifest
        manifest_path = os.path.join(current_dir, 'FusionTimekeeper.manifest')
        if not os.path.exists(manifest_path):
            print("Error: FusionTimekeeper.manifest not found!")
            return False

        # Get the add-ins directory
        addin_dir = get_addin_path()
        if not os.path.exists(addin_dir):
            print(f"Error: Add-ins directory not found at {addin_dir}")
            return False

        # Create the destination directory
        dest_dir = os.path.join(addin_dir, 'FusionTimekeeper')
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
        os.makedirs(dest_dir)

        # Copy all files to the destination
        for item in os.listdir(current_dir):
            s = os.path.join(current_dir, item)
            d = os.path.join(dest_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        print(f"Add-in installed successfully to {dest_dir}")
        return True

    except Exception as e:
        print(f"Error installing add-in: {str(e)}")
        return False

if __name__ == '__main__':
    if install_addin():
        print("Installation completed successfully!")
    else:
        print("Installation failed!")
        sys.exit(1) 