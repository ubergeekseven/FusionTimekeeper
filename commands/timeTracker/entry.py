import adsk.core
import adsk.fusion
import traceback
import os
import sys

# Add the lib directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.abspath(os.path.join(current_dir, '..', '..', 'lib'))
if lib_dir not in sys.path:
    sys.path.append(lib_dir)

from timeTrackerUtils.time_tracker import TimeTracker
from timeTrackerUtils.ui.main_window import TimeTrackerWindow

# Command identity information
CMD_ID = 'FusionTimekeeper'
CMD_NAME = 'Time Tracker'
CMD_DESCRIPTION = 'Track time spent on your Fusion 360 projects'

# Specify that the command will be promoted to the panel
IS_PROMOTED = True

# Define the location where the command button will be created
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# Resource location for command icons
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')

# Global command instance
_cmd = None

def start():
    global _cmd
    try:
        _cmd = FusionTimekeeperCommand()
        _cmd.start()
    except:
        if adsk.core.Application.get():
            adsk.core.Application.get().userInterface.messageBox(
                'Failed to start:\n{}'.format(traceback.format_exc())
            )

def stop():
    global _cmd
    try:
        if _cmd and _cmd.window:
            _cmd.window.palette.deleteMe()
    except:
        if adsk.core.Application.get():
            adsk.core.Application.get().userInterface.messageBox(
                'Failed to stop:\n{}'.format(traceback.format_exc())
            )

class TimeTrackerCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, time_tracker):
        super().__init__()
        self.time_tracker = time_tracker
        self.window = None

    def notify(self, args):
        try:
            # Create and show the time tracker window
            self.window = TimeTrackerWindow(self.time_tracker)
            self.window.show()
        except:
            if adsk.core.Application.get():
                adsk.core.Application.get().userInterface.messageBox(
                    'Failed to create command:\n{}'.format(traceback.format_exc())
                )

class FusionTimekeeperCommand:
    def __init__(self):
        self.app = adsk.core.Application.get()
        self.ui = self.app.userInterface
        self.time_tracker = TimeTracker()
        self.window = None
        self.handlers = []
        self.cmd_def = None

    def start(self):
        try:
            # Check if the command definition already exists
            cmd_defs = self.ui.commandDefinitions
            self.cmd_def = cmd_defs.itemById(CMD_ID)
            if self.cmd_def:
                self.cmd_def.deleteMe()
            
            # Create the command definition
            self.cmd_def = cmd_defs.addButtonDefinition(
                CMD_ID,
                CMD_NAME,
                CMD_DESCRIPTION,
                ICON_FOLDER
            )

            # Get the target workspace
            workspace = self.ui.workspaces.itemById(WORKSPACE_ID)
            if workspace:
                # Get the panel
                panel = workspace.toolbarPanels.itemById(PANEL_ID)
                if panel:
                    # Create the button command control in the UI
                    control = panel.controls.addCommand(self.cmd_def, '', False)
                    # Specify if the command is promoted to the main toolbar
                    control.isPromoted = IS_PROMOTED

                    # Create and add the command created handler
                    handler = TimeTrackerCommandCreatedHandler(self.time_tracker)
                    self.cmd_def.commandCreated.add(handler)
                    self.handlers.append(handler)
                else:
                    self.ui.messageBox(f'Panel {PANEL_ID} not found')
            else:
                self.ui.messageBox(f'Workspace {WORKSPACE_ID} not found')

        except:
            if self.ui:
                self.ui.messageBox('Failed to start:\n{}'.format(traceback.format_exc())) 