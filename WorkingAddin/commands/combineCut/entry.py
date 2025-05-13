import adsk.core
import os
from ...lib import fusionAddInUtils as futil
from ... import config
app = adsk.core.Application.get()
ui = app.userInterface


# Command identity information.
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_combineCut'
CMD_NAME = 'Combine Cut'
CMD_Description = 'Cuts tool components from target components'

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# Define the location where the command button will be created.
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidModifyPanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []

# Keep track of the number of pairs
pair_count = 1


# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar. 
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    global pair_count
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Created Event')

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs
    group = inputs.addGroupCommandInput('pairs_group', 'Target/Tool Pairs')
    group_inputs = group.children
    # Add the first pair
    group_inputs.addSelectionInput(f'plate_0', 'Target Component', 'Select the target component').addSelectionFilter('Occurrences')
    group_inputs.itemById(f'plate_0').setSelectionLimits(1, 1)
    group_inputs.addSelectionInput(f'text_0', 'Tool Component', 'Select the tool component').addSelectionFilter('Occurrences')
    group_inputs.itemById(f'text_0').setSelectionLimits(1, 1)
    # Add + button
    inputs.addBoolValueInput('add_pair', 'Add Pair', False, '', False)
    # Add Save and Load buttons
    inputs.addBoolValueInput('save_pairs', 'Save Pairs', False, '', False)
    inputs.addBoolValueInput('load_pairs', 'Load Pairs', False, '', False)
    # Add Info button
    inputs.addBoolValueInput('info', 'Why manual selection?', False, '', False)

    # Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Event')
    inputs = args.command.commandInputs
    group = inputs.itemById('pairs_group')
    group_inputs = group.children
    pairs = []
    for idx in range(pair_count):
        plate_input = group_inputs.itemById(f'plate_{idx}')
        text_input = group_inputs.itemById(f'text_{idx}')
        if not plate_input or not text_input:
            continue
        if plate_input.selectionCount == 0 or text_input.selectionCount == 0:
            continue
        plate_occurrence = plate_input.selection(0).entity
        text_occurrence = text_input.selection(0).entity
        pairs.append((plate_occurrence, text_occurrence))
    design = adsk.fusion.FusionDocument.cast(app.activeDocument).design
    root = design.rootComponent
    for plate_occurrence, text_occurrence in pairs:
        plate_component = plate_occurrence.component
        plate_body = plate_component.bRepBodies.itemByName(plate_component.name)
        text_component = text_occurrence.component
        if not plate_body:
            ui.messageBox(f'Target body "{plate_component.name}" not found')
            continue
        if not text_component:
            ui.messageBox(f'Tool component "{text_component.name}" not found')
            continue
        tool_bodies = adsk.core.ObjectCollection.create()
        for body in text_component.bRepBodies:
            tool_bodies.add(body)
        combine_features = root.features.combineFeatures
        combine_input = combine_features.createInput(plate_body, tool_bodies)
        combine_input.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
        combine_input.isKeepToolBodies = True
        combine_features.add(combine_input)
    ui.messageBox('Combine/Cut operation completed successfully for all pairs')


# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Preview Event')
    inputs = args.command.commandInputs


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    import json
    global pair_count
    changed_input = args.input
    inputs = args.inputs
    group = inputs.itemById('pairs_group')
    if not group:
        return
    group_inputs = group.children
    if changed_input.id == 'add_pair':
        pair_count += 1
        idx = pair_count - 1
        plate_input = group_inputs.addSelectionInput(f'plate_{idx}', f'Target Component {idx+1}', 'Select the target component')
        plate_input.addSelectionFilter('Occurrences')
        plate_input.setSelectionLimits(1, 1)
        group_inputs.addTextBoxCommandInput(f'plate_name_{idx}', '', '', 1, True)
        text_input = group_inputs.addSelectionInput(f'text_{idx}', f'Tool Component {idx+1}', 'Select the tool component')
        text_input.addSelectionFilter('Occurrences')
        text_input.setSelectionLimits(1, 1)
        group_inputs.addTextBoxCommandInput(f'text_name_{idx}', '', '', 1, True)
        changed_input.value = False
    elif changed_input.id == 'save_pairs':
        changed_input.value = False
        pairs = []
        for i in range(0, len(group_inputs), 2):
            plate_input = group_inputs.item(i)
            text_input = group_inputs.item(i+1)
            if plate_input.selectionCount == 0 or text_input.selectionCount == 0:
                continue
            plate_name = plate_input.selection(0).entity.component.name
            text_name = text_input.selection(0).entity.component.name
            pairs.append({"plate": plate_name, "text": text_name})
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plate_text_pairs.json')
        with open(save_path, 'w') as f:
            json.dump(pairs, f)
        ui.messageBox(f'Saved {len(pairs)} pairs.')
    elif changed_input.id == 'load_pairs':
        changed_input.value = False
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plate_text_pairs.json')
        if not os.path.exists(save_path):
            ui.messageBox('No saved pairs found.')
            return
        with open(save_path, 'r') as f:
            pairs = json.load(f)
        # Clear current inputs
        for i in reversed(range(group_inputs.count)):
            group_inputs.item(i).deleteMe()
        # Add loaded pairs with tooltips and default text
        for idx, pair in enumerate(pairs):
            plate_input = group_inputs.addSelectionInput(f'plate_{idx}', f'Target Component {idx+1}', f'Select the target component (saved: {pair["plate"]})')
            plate_input.addSelectionFilter('Occurrences')
            plate_input.setSelectionLimits(1, 1)
            plate_input.tooltip = f'Select the target component named: {pair["plate"]}'
            plate_input.prompt = f'Saved: {pair["plate"]}'
            group_inputs.addTextBoxCommandInput(f'plate_name_{idx}', '', pair["plate"], 1, True)
            text_input = group_inputs.addSelectionInput(f'text_{idx}', f'Tool Component {idx+1}', f'Select the tool component (saved: {pair["text"]})')
            text_input.addSelectionFilter('Occurrences')
            text_input.setSelectionLimits(1, 1)
            text_input.tooltip = f'Select the tool component named: {pair["text"]}'
            text_input.prompt = f'Saved: {pair["text"]}'
            group_inputs.addTextBoxCommandInput(f'text_name_{idx}', '', pair["text"], 1, True)
        pair_count = len(pairs) if pairs else 1
        ui.messageBox(f'Loaded {len(pairs)} pairs. Please reselect the components in the UI.')
    elif changed_input.id == 'info':
        changed_input.value = False
        ui.messageBox('It is annoying, I know. Fusion 360 does not allow add-ins to automatically select components in the UI.\n\nYou must manually reselect the components for each pair. The saved names are shown to help you choose the correct ones.')
    # Update text boxes when a selection changes
    if changed_input.id.startswith('plate_') or changed_input.id.startswith('text_'):
        # Find the index
        if '_' in changed_input.id:
            prefix, idx = changed_input.id.split('_', 1)
            name_box_id = f'{prefix}_name_{idx}'
            name_box = group_inputs.itemById(name_box_id)
            if name_box:
                if changed_input.selectionCount > 0:
                    name_box.text = changed_input.selection(0).entity.component.name
                else:
                    name_box.text = ''
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    inputs = args.inputs
    group = inputs.itemById('pairs_group')
    group_inputs = group.children
    valid = True
    for idx in range(pair_count):
        plate_input = group_inputs.itemById(f'plate_{idx}')
        text_input = group_inputs.itemById(f'text_{idx}')
        if not plate_input or not text_input:
            valid = False
            break
        if plate_input.selectionCount == 0 or text_input.selectionCount == 0:
            valid = False
            break
    args.areInputsValid = valid


# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers, pair_count
    local_handlers = []
    pair_count = 1 