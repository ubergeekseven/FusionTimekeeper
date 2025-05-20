import adsk.core
import adsk.fusion
import traceback
import json
import os
from ..parameter_storage import ParameterStorage

class PaletteClosedHandler(adsk.core.UserInterfaceGeneralEventHandler):
    def __init__(self, window):
        super().__init__()
        self.window = window

    def notify(self, args):
        try:
            if self.window.palette:
                self.window.palette.deleteMe()
                self.window.palette = None
        except:
            if self.window.ui:
                self.window.ui.messageBox('Failed to close palette:\n{}'.format(traceback.format_exc()))

class PaletteHTMLEventHandler(adsk.core.HTMLEventHandler):
    def __init__(self, window):
        super().__init__()
        self.window = window

    def notify(self, args):
        try:
            html_args = adsk.core.HTMLEventArgs.cast(args)
            print(f"Received HTML event in Notes: {html_args.data}")
            data = json.loads(html_args.data)
            action = data.get('action', '')
            print(f"Processing notes action: {action}")
            
            if action == 'loadNotes':
                # Load notes from parameters
                print("Attempting to load notes from parameters")
                notes = ParameterStorage.retrieve_notes_data()
                if notes is not None:
                    print(f"Notes loaded, length: {len(notes)}")
                    self.window.palette.sendInfoToHTML('notesLoaded', json.dumps({"notes": notes}))
                else:
                    print("No notes found, sending empty string")
                    self.window.palette.sendInfoToHTML('notesLoaded', json.dumps({"notes": ""}))
            
            elif action == 'saveNotes':
                # Save notes to parameters
                print("Attempting to save notes to parameters")
                notes = data.get('notes', '')
                print(f"Notes to save, length: {len(notes)}")
                success = ParameterStorage.store_notes_data(notes)
                print(f"Save notes result: {'success' if success else 'failed'}")
                self.window.palette.sendInfoToHTML('notesSaved', json.dumps({"success": success}))
            
            elif action == 'getProjectInfo':
                # Get current project information
                print("Retrieving project info for notes")
                project_info = self.window.get_project_info()
                print(f"Project info for notes: {project_info}")
                self.window.palette.sendInfoToHTML('projectInfo', json.dumps(project_info))
                
        except Exception as e:
            print(f"Notes HTML Event Error: {str(e)}")
            print(f"Notes Traceback: {traceback.format_exc()}")
            if self.window.ui:
                self.window.ui.messageBox('HTML Event Error:\n{}'.format(traceback.format_exc()))

class NotesWindow:
    def __init__(self):
        self.app = adsk.core.Application.get()
        self.ui = self.app.userInterface
        self.palette = None
        self.closed_handler = None
        self.html_handler = None

    def show(self):
        try:
            palette_id = 'NotesPalette'
            palette_name = 'Notes'
            html_path = 'commands/timeTracker/resources/NotesPalette.html'
            self.palette = self.ui.palettes.itemById(palette_id)
            if not self.palette:
                self.palette = self.ui.palettes.add(
                    palette_id,
                    palette_name,
                    html_path,
                    True,  # isVisible
                    True,  # showCloseButton
                    True,  # isResizable
                    420,   # width
                    400    # height
                )
                self.closed_handler = PaletteClosedHandler(self)
                self.palette.closed.add(self.closed_handler)
                
                # Add HTML event handler
                self.html_handler = PaletteHTMLEventHandler(self)
                self.palette.incomingFromHTML.add(self.html_handler)
                
                # Set additional options
                self.palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateRight
                self.palette.dockingOption = adsk.core.PaletteDockingOptions.PaletteDockOptionsToVerticalOnly
                
            self.palette.isVisible = True
        except:
            if self.ui:
                self.ui.messageBox('Failed to show notes window:\n{}'.format(traceback.format_exc()))
    
    def get_project_info(self):
        """Get information about the current Fusion 360 project."""
        try:
            # Get active document
            doc = self.app.activeDocument
            if not doc:
                return {"name": "No active document", "id": ""}
            
            # Get document name and ID
            return {
                "name": doc.name,
                "id": doc.dataFile.id if doc.dataFile else "",
                "path": doc.dataFile.fullPath if doc.dataFile else ""
            }
        except:
            return {"name": "Error getting project info", "id": ""} 