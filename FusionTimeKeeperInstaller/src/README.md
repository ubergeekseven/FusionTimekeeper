# Fusion Timekeeper

A Fusion 360 add-in for tracking time spent on design projects. This add-in allows you to:
- Track time spent on individual Fusion 360 projects
- View session history with start/end times
- Export time data to CSV or text files
- Maintain separate time tracking for each project
- Automatically save and restore time tracking data

## Installation

### For End Users
1. Download the latest release ZIP file
2. Extract the ZIP file to a temporary location
3. Run the `install.bat` file (Windows) or use the manual installation process (Mac)
4. Follow the on-screen instructions

### For Developers
1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy the entire project folder to your Fusion 360 add-ins directory:
   - Windows: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns`
   - Mac: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns`

## Distribution

To create a distribution package for end users:
1. Run the packaging script:
   ```
   python package.py
   ```
2. The script will create a `dist` folder containing:
   - A folder with all necessary files for the add-in
   - An `install.bat` file for easy installation
   - A ZIP file ready for distribution

## Usage

1. Launch Fusion 360
2. The Timekeeper icon will appear in the Design toolbar
3. Click the icon to open the Timekeeper window
4. Use the Start/Stop button to track time
5. View your session history in the table
6. Export your time data using the Export buttons

## Features

- Real-time timer display
- Session history tracking
- Project-specific time tracking
- CSV and text file export
- Automatic data persistence
- Clean, modern user interface

## Data Storage

Time tracking data is stored in a `.timekeeper` directory within each project's folder. The data is stored in an SQLite database, making it:
- Reliable and consistent
- Easy to backup
- Project-specific
- Automatically saved

## Requirements

- Fusion 360
- Python 3.7 or higher
- PyQt5
- pandas
