import adsk.core
import adsk.fusion
import traceback
import os
import sys

# Add the commands directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from . import commands
from .lib import fusionAddInUtils as futil

def run(context):
    try:
        # Initialize logging
        futil.log_info("FusionTimekeeper add-in starting")
        futil.log_info(f"Current directory: {current_dir}")
        
        # Set debug mode from environment variable if available
        debug_mode = os.environ.get('FUSION_TIMEKEEPER_DEBUG', 'False').lower() == 'true'
        futil.enable_debug_mode(debug_mode)
        
        # Log some basic system information
        app = adsk.core.Application.get()
        if app:
            futil.log_info(f"Fusion 360 version: {app.version}")
        
        # This will run the start function in each of your commands as defined in commands/__init__.py
        commands.start()
        futil.log_info("FusionTimekeeper add-in started successfully")

    except:
        futil.handle_error('run')


def stop(context):
    try:
        futil.log_info("FusionTimekeeper add-in stopping")
        
        # Remove all of the event handlers your app has created
        futil.clear_handlers()

        # This will run the start function in each of your commands as defined in commands/__init__.py
        commands.stop()
        
        futil.log_info("FusionTimekeeper add-in stopped successfully")

    except:
        futil.handle_error('stop') 