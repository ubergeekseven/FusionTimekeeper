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
# We'll import NotesWindow after it's created
try:
    from timeTrackerUtils.ui.notes_window import NotesWindow
except ImportError:
    NotesWindow = None

# Command identity information
CMD_ID = 'FusionTimekeeper'
CMD_NAME = 'Time Tracker'
CMD_DESCRIPTION = 'Track time spent on your Fusion 360 projects'

NOTES_CMD_ID = 'FusionNotes'
NOTES_CMD_NAME = 'Notes'
NOTES_CMD_DESCRIPTION = 'Project notes and scratchpad'

# Specify that the command will be promoted to the panel
IS_PROMOTED = True

# Define the location where the command button will be created
WORKSPACE_ID = 'FusionSolidEnvironment'  # Design workspace (Solid)
TAB_ID = 'SolidTab'                      # The built-in Solid tab

# Define our custom panel within the Solid tab
CUSTOM_PANEL_ID = 'TimeTrackerPanel'
CUSTOM_PANEL_NAME = 'Time Tracking'

# Resource locations for command icons
TIMEKEEPER_ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'timekeeper_icon')
NOTES_ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'notes_icon')

# Global command instances
_cmd = None
_notes_cmd = None

def start():
    global _cmd, _notes_cmd
    try:
        _cmd = FusionTimekeeperCommand()
        _cmd.start()
        _notes_cmd = NotesCommand()
        _notes_cmd.start()
    except:
        if adsk.core.Application.get():
            adsk.core.Application.get().userInterface.messageBox(
                'Failed to start:\n{}'.format(traceback.format_exc())
            )

def stop():
    global _cmd, _notes_cmd
    try:
        if _cmd and _cmd.window:
            _cmd.window.palette.deleteMe()
        if _notes_cmd and _notes_cmd.window:
            _notes_cmd.window.palette.deleteMe()
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
            self.window = TimeTrackerWindow(self.time_tracker)
            self.window.show()
        except:
            if adsk.core.Application.get():
                adsk.core.Application.get().userInterface.messageBox(
                    'Failed to create command:\n{}'.format(traceback.format_exc())
                )

class NotesCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
        self.window = None

    def notify(self, args):
        try:
            if NotesWindow:
                self.window = NotesWindow()
                self.window.show()
            else:
                adsk.core.Application.get().userInterface.messageBox('NotesWindow not implemented yet.')
        except:
            if adsk.core.Application.get():
                adsk.core.Application.get().userInterface.messageBox(
                    'Failed to create notes command:\n{}'.format(traceback.format_exc())
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
            cmd_defs = self.ui.commandDefinitions
            self.cmd_def = cmd_defs.itemById(CMD_ID)
            if self.cmd_def:
                self.cmd_def.deleteMe()
            self.cmd_def = cmd_defs.addButtonDefinition(
                CMD_ID,
                CMD_NAME,
                CMD_DESCRIPTION,
                TIMEKEEPER_ICON_FOLDER
            )
            workspace = self.ui.workspaces.itemById(WORKSPACE_ID)
            if workspace:
                # First, check all panels for existing controls with our CMD_ID and remove them
                for tab in workspace.toolbarTabs:
                    for panel in tab.toolbarPanels:
                        for i in range(panel.controls.count):
                            try:
                                if panel.controls.item(i).id == CMD_ID:
                                    panel.controls.item(i).deleteMe()
                                    break
                            except:
                                # Skip any errors (control might be of a type that doesn't have an id)
                                pass
                
                tab = workspace.toolbarTabs.itemById(TAB_ID)
                if tab:
                    # Create our own panel in the Solid tab
                    panel = tab.toolbarPanels.itemById(CUSTOM_PANEL_ID)
                    if not panel:
                        panel = tab.toolbarPanels.add(CUSTOM_PANEL_ID, CUSTOM_PANEL_NAME)
                    
                    # Remove any existing controls with our ID
                    for i in range(panel.controls.count):
                        if panel.controls.item(i).id == CMD_ID:
                            panel.controls.item(i).deleteMe()
                            break
                    
                    # Add the command to our custom panel
                    control = panel.controls.addCommand(self.cmd_def)
                    control.isPromoted = IS_PROMOTED
                    handler = TimeTrackerCommandCreatedHandler(self.time_tracker)
                    self.cmd_def.commandCreated.add(handler)
                    self.handlers.append(handler)
                else:
                    self.ui.messageBox(f'Tab {TAB_ID} not found')
            else:
                self.ui.messageBox(f'Workspace {WORKSPACE_ID} not found')
        except:
            if self.ui:
                self.ui.messageBox('Failed to start:\n{}'.format(traceback.format_exc()))

class NotesCommand:
    def __init__(self):
        self.app = adsk.core.Application.get()
        self.ui = self.app.userInterface
        self.window = None
        self.handlers = []
        self.cmd_def = None

    def start(self):
        try:
            cmd_defs = self.ui.commandDefinitions
            self.cmd_def = cmd_defs.itemById(NOTES_CMD_ID)
            if self.cmd_def:
                self.cmd_def.deleteMe()
            self.cmd_def = cmd_defs.addButtonDefinition(
                NOTES_CMD_ID,
                NOTES_CMD_NAME,
                NOTES_CMD_DESCRIPTION,
                NOTES_ICON_FOLDER
            )
            workspace = self.ui.workspaces.itemById(WORKSPACE_ID)
            if workspace:
                # First, check all panels for existing controls with our NOTES_CMD_ID and remove them
                for tab in workspace.toolbarTabs:
                    for panel in tab.toolbarPanels:
                        for i in range(panel.controls.count):
                            try:
                                if panel.controls.item(i).id == NOTES_CMD_ID:
                                    panel.controls.item(i).deleteMe()
                                    break
                            except:
                                # Skip any errors (control might be of a type that doesn't have an id)
                                pass
                
                tab = workspace.toolbarTabs.itemById(TAB_ID)
                if tab:
                    # Use our custom panel in the Solid tab
                    panel = tab.toolbarPanels.itemById(CUSTOM_PANEL_ID)
                    if not panel:
                        panel = tab.toolbarPanels.add(CUSTOM_PANEL_ID, CUSTOM_PANEL_NAME)
                    
                    # Remove any existing controls with our ID
                    for i in range(panel.controls.count):
                        if panel.controls.item(i).id == NOTES_CMD_ID:
                            panel.controls.item(i).deleteMe()
                            break
                    
                    # Add the command to our custom panel
                    control = panel.controls.addCommand(self.cmd_def)
                    control.isPromoted = IS_PROMOTED
                    handler = NotesCommandCreatedHandler()
                    self.cmd_def.commandCreated.add(handler)
                    self.handlers.append(handler)
                else:
                    self.ui.messageBox(f'Tab {TAB_ID} not found')
            else:
                self.ui.messageBox(f'Workspace {WORKSPACE_ID} not found')
        except:
            if self.ui:
                self.ui.messageBox('Failed to start notes command:\n{}'.format(traceback.format_exc())) 