import adsk.core
import adsk.fusion
import traceback
import json
from datetime import datetime
import sys
import os

# Add the lib directory to path if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
if lib_dir not in sys.path:
    sys.path.append(lib_dir)

from ..parameter_storage import ParameterStorage
from fusionAddInUtils import log_info, log_debug, log_warning, log_error

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
                log_error(f"Failed to close palette: {traceback.format_exc()}")

class PaletteHTMLEventHandler(adsk.core.HTMLEventHandler):
    def __init__(self, window):
        super().__init__()
        self.window = window

    def notify(self, args):
        try:
            html_args = adsk.core.HTMLEventArgs.cast(args)
            
            # Debug raw data
            raw_data = html_args.data
            action = html_args.action  # Get the action directly
            
            # # SHOW A MESSAGE BOX FOR EVERY ACTION - This will confirm we're receiving events
            # try:
            #     msg = f"PALETTE EVENT RECEIVED:\nAction: {action}\nData: {raw_data[:50] if raw_data else 'None'}"
            #     self.window.ui.messageBox(msg)
            # except:
            #     pass  # Ignore errors from message box
                
            log_info(f"\n=== HTML EVENT: {action} ===")
            log_debug(f"Raw data: '{raw_data}'")
            
            # Skip empty events but DO NOT return early
            # Some events may have empty data but valid actions
            if action:
                log_info(f"Processing action: '{action}'")
                
                # Process based on action name
                if action == 'simpleTest':
                    self.handle_simple_test(html_args)
                    
                elif action == 'updateParam':
                    self.handle_param_update(html_args)
                    
                elif action == 'loadTimeData':
                    # Load time data from parameters
                    log_info("loadTimeData action received")
                    self.handle_load_time_data(html_args)
                    
                elif action == 'saveTimeData':
                    self.handle_save_time_data(html_args)
                    
                elif action == 'getProjectInfo':
                    self.handle_project_info(html_args)
                
                elif action == 'paletteLoaded':
                    # Return initial parameter values on palette load
                    self.handle_palette_loaded(html_args)
                    
                elif action == 'readParameters':
                    # Get a test ID from data if available
                    test_id = "unknown"
                    try:
                        if html_args.data:
                            data = json.loads(html_args.data)
                            test_id = data.get('testId', test_id)
                    except:
                        pass
                    
                    # Get the active document
                    design = ParameterStorage.get_active_document()
                    if design:
                        self.handle_read_parameter_test(html_args, test_id, design)
                    else:
                        self.send_response(args, {
                            "success": False,
                            "testId": test_id,
                            "message": "No active document found!"
                        })
                
                elif action == 'readRawParameters':
                    # Return raw parameter data for debugging
                    self.handle_raw_parameters(html_args)
                    
                else:
                    log_warning(f"Unknown action received: '{action}'")
                    # Return a generic error response for unknown actions
                    self.send_response(args, {
                        "success": False, 
                        "message": f"Unknown action: {action}"
                    })
            else:
                log_info("Empty action received, ignoring")
            
        except Exception as e:
            log_error(f"HTML Event Error: {str(e)}")
            log_debug(f"Traceback: {traceback.format_exc()}")
            if self.window.ui:
                self.window.ui.messageBox('HTML Event Error:\n{}'.format(traceback.format_exc()))
    
    def send_response(self, args, data):
        """Helper to safely send JSON responses."""
        try:
            log_info("Serializing response to JSON...")
            json_string = json.dumps(data)
            log_info(f"Response JSON length: {len(json_string)}")
            
            # For debugging, show the first part of the response
            log_debug(f"Response JSON start: {json_string[:100]}..." if len(json_string) > 100 else json_string)
            
            # Set the return data
            log_info("Setting returnData on args")
            
            # IMPORTANT: Make sure we're using the correct property name for HTML events
            html_args = adsk.core.HTMLEventArgs.cast(args)
            if html_args:
                html_args.returnData = json_string
                log_info("Response set using HTMLEventArgs.returnData")
            else:
                args.returnData = json_string
                log_info("Response set using args.returnData (not cast)")
                
            log_info("Response sent successfully")
            return True
        except json.JSONDecodeError as je:
            log_error(f"JSON encoding error: {str(je)}")
            log_debug(f"Failed data structure: {str(data)[:200]}...")
            
            # Try to send a simple error response instead
            try:
                args.returnData = json.dumps({
                    "success": False,
                    "message": f"Error encoding response: {str(je)}"
                })
                log_warning("Sent error response instead")
            except:
                # Last resort - send a hardcoded string
                args.returnData = '{"success":false,"message":"Critical JSON encoding error"}'
                log_error("Sent hardcoded error response")
            return False
        except Exception as e:
            log_error(f"Error sending response: {str(e)}")
            log_debug(f"Traceback: {traceback.format_exc()}")
            log_debug(f"Failed data structure: {str(data)[:200]}...")
            
            # Try to send a simple error response instead
            try:
                args.returnData = json.dumps({
                    "success": False,
                    "message": f"Error sending response: {str(e)}"
                })
                log_warning("Sent error response instead")
            except:
                # Last resort - send a hardcoded string
                args.returnData = '{"success":false,"message":"Critical error sending response"}'
                log_error("Sent hardcoded error response")
            return False
    
    def handle_simple_test(self, args):
        """Handle simple parameter test."""
        try:
            # Parse data if available
            data = {}
            if args.data and args.data.strip():
                try:
                    data = json.loads(args.data)
                    log_debug(f"Parsed test data: {data}")
                except json.JSONDecodeError as je:
                    log_error(f"JSON parse error: {je}")
                    log_debug(f"Raw data: '{args.data}'")
            else:
                log_warning("Warning: Empty data received in simple test")
            
            test_id = data.get('testId', str(datetime.now().strftime("%H%M%S")))
            test_value = data.get('value', f'Simple test at {datetime.now().strftime("%H:%M:%S")}')
            command = data.get('command', 'createParameter')
            
            log_info(f"[{test_id}] Simple parameter test - command: {command}")
            
            # Get active document and create parameter
            design = ParameterStorage.get_active_document()
            if not design:
                log_error(f"[{test_id}] No active document!")
                # Set return value for immediate response
                self.send_response(args, {
                    "success": False,
                    "testId": test_id,
                    "message": "No active document found!"
                })
                return
                
            # Handle different commands
            if command == 'readParameter':
                self.handle_read_parameter_test(args, test_id, design)
                return
                
            # Get parameters collection
            params = design.userParameters
            log_debug(f"[{test_id}] Parameters count: {params.count}")
            
            # Create a test parameter
            param_name = f'SimpleTest{test_id}'
            log_info(f"[{test_id}] Creating parameter: {param_name}")
            
            # First try to get existing parameter
            test_param = params.itemByName(param_name)
            if test_param:
                # Update existing parameter
                # Properly escape any quotes in the test value
                escaped_value = test_value.replace('"', '\\"')
                test_param.expression = f'"{escaped_value}"'
                log_info(f"[{test_id}] Updated parameter: {param_name}")
            else:
                # Create new parameter
                # Properly escape any quotes in the test value
                escaped_value = test_value.replace('"', '\\"')
                test_param = params.add(
                    param_name, 
                    adsk.core.ValueInput.createByString(f'"{escaped_value}"'),
                    '', 
                    f'Test parameter created at {datetime.now().strftime("%H:%M:%S")}'
                )
                log_info(f"[{test_id}] Created parameter: {param_name}")
                
            if test_param:
                # Return success immediately
                self.send_response(args, {
                    "success": True,
                    "testId": test_id,
                    "message": f"Parameter {param_name} created successfully!"
                })
                log_info(f"[{test_id}] Test completed successfully")
            else:
                self.send_response(args, {
                    "success": False,
                    "testId": test_id,
                    "message": "Failed to create parameter"
                })
                log_error(f"[{test_id}] Failed to create parameter")
                
        except Exception as e:
            log_error(f"Simple test error: {str(e)}")
            log_debug(f"Traceback: {traceback.format_exc()}")
            self.send_response(args, {
                "success": False,
                "message": f"Error: {str(e)}"
            })
    
    def handle_read_parameter_test(self, args, test_id, design):
        """Test reading a parameter."""
        try:
            log_info(f"[{test_id}] Reading parameters test")
            
            # Get parameters collection
            params = design.userParameters
            log_debug(f"[{test_id}] Total parameters: {params.count}")
            
            # List all parameters
            param_list = []
            for i in range(params.count):
                param = params.item(i)
                # Ensure all values are JSON serializable
                param_value = None
                try:
                    # Convert any non-serializable value to string
                    if isinstance(param.value, (int, float)):
                        param_value = param.value
                    else:
                        param_value = str(param.value)
                except:
                    param_value = "Error getting value"
                
                param_list.append({
                    'name': param.name,
                    'expression': param.expression,
                    'value': param_value,
                    'comment': param.comment
                })
                
            log_info(f"[{test_id}] Found {len(param_list)} parameters")
            
            # Read test parameters
            test_params = [p for p in param_list if p['name'].startswith('SimpleTest')]
            log_info(f"[{test_id}] Found {len(test_params)} test parameters")
            
            # Create response JSON with basic stringification safety
            response_data = {
                "success": True,
                "testId": test_id,
                "message": f"Found {len(test_params)} test parameters",
                "parameters": param_list,
                "testParameters": test_params
            }
            
            # Send the response
            self.send_response(args, response_data)
            
        except Exception as e:
            log_error(f"[{test_id}] Read parameter test error: {str(e)}")
            log_debug(f"Traceback: {traceback.format_exc()}")
            self.send_response(args, {
                "success": False,
                "testId": test_id,
                "message": f"Error reading parameters: {str(e)}"
            })
    
    def handle_param_update(self, args):
        """Handle parameter updates from UI."""
        try:
            if not args.data:
                log_warning("Empty data in param_update request")
                return
                
            data = json.loads(args.data)
            param_name = data.get('parameter')
            param_value = data.get('value')
            
            if not param_name or param_value is None:
                log_warning("Missing parameter name or value")
                return
                
            design = ParameterStorage.get_active_document()
            if not design:
                log_error("No active document in param_update")
                return
                
            params = design.userParameters
            param = params.itemByName(param_name)
            
            if param:
                log_info(f"Updating parameter: {param_name} = {param_value}")
                
                # Determine if value is string or number
                if isinstance(param_value, str):
                    escaped_value = param_value.replace('"', '\\"')
                    param.expression = f'"{escaped_value}"'
                else:
                    param.expression = str(param_value)
                    
                self.send_response(args, {
                    "success": True,
                    "message": f"Updated parameter {param_name}"
                })
            else:
                log_warning(f"Parameter not found: {param_name}")
                self.send_response(args, {
                    "success": False,
                    "message": f"Parameter {param_name} not found"
                })
                
        except Exception as e:
            log_error(f"Parameter update error: {str(e)}")
            log_debug(f"Traceback: {traceback.format_exc()}")
            self.send_response(args, {
                "success": False,
                "message": f"Error: {str(e)}"
            })
    
    def handle_palette_loaded(self, args):
        """Handle the palette loaded event to initialize data."""
        try:
            log_info("\n=== PALETTE LOADED EVENT ===")
            log_info("Initializing palette with parameter data")
            
            design = ParameterStorage.get_active_document()
            if not design:
                log_error("No active document for palette load")
                self.send_response(args, {
                    "success": False,
                    "message": "No active document found",
                    "timeData": {"timeTracker": {"sessions": []}}
                })
                return
            
            # Get project info
            project_info = self.window.get_project_info()
            log_debug(f"Project info: {project_info}")
            
            # Debug available parameters
            params = design.userParameters
            log_info(f"Found {params.count} total parameters")
            
            # List all parameters for debugging
            param_names = []
            for i in range(params.count):
                param = params.item(i)
                param_names.append(f"{param.name} ({param.value})")
            log_info(f"Parameters: {', '.join(param_names)}")
            
            # Get time parameters names
            time_params = []
            for i in range(params.count):
                param = params.item(i)
                if param.name == ParameterStorage.TIME_DATA_PARAM or param.name.startswith(ParameterStorage.TIME_PREFIX):
                    time_params.append(param.name)
            
            if time_params:
                log_info(f"Found time parameters: {', '.join(time_params)}")
                # Retrieve time data from parameters
                time_data = ParameterStorage.retrieve_time_data()
            else:
                log_warning("No time parameters found in document")
                time_data = {"timeTracker": {"sessions": []}}
            
            # Always ensure we have a valid structure
            if not time_data or not isinstance(time_data, dict):
                log_warning("Invalid time data returned, using empty structure")
                time_data = {"timeTracker": {"sessions": []}}
                
            if 'timeTracker' not in time_data:
                log_warning("No timeTracker key in data, adding empty structure")
                time_data['timeTracker'] = {"sessions": []}
                
            if 'sessions' not in time_data['timeTracker']:
                log_warning("No sessions key in timeTracker data, adding empty array")
                time_data['timeTracker']['sessions'] = []
                
            # If valid time data exists, log some debug info
            session_count = len(time_data['timeTracker']['sessions'])
            log_info(f"Retrieved time data with {session_count} sessions for palette load")
            
            # Print detailed info about the time data
            for i, session in enumerate(time_data['timeTracker']['sessions']):
                log_info(f"Session {i+1}: Date: {session.get('date', 'unknown')}, Times count: {len(session.get('times', []))}")
                if 'times' in session and len(session['times']) > 0:
                    log_debug(f"  First time value: {session['times'][0]} seconds")
            
            # Create a response with both project info and time data
            response = {
                "success": True,
                "timeData": time_data,
                "projectInfo": project_info
            }
            
            # Debug the response
            response_json = json.dumps(response)
            log_debug(f"Response JSON length: {len(response_json)}")
            log_debug(f"First 100 chars: {response_json[:100]}...")
            
            # Send the response
            log_info("Sending initial palette data")
            self.send_response(args, response)
            log_info("=== END PALETTE LOADED EVENT ===\n")
            
        except Exception as e:
            log_error(f"Palette load error: {str(e)}")
            log_debug(f"Traceback: {traceback.format_exc()}")
            self.send_response(args, {
                "success": False,
                "message": f"Error loading palette data: {str(e)}",
                "timeData": {"timeTracker": {"sessions": []}}
            })
    
    def handle_load_time_data(self, args):
        """Handle loading time data."""
        try:
            log_info("\n=== LOAD TIME DATA REQUEST ===")
            log_info("Loading time data from parameters")
            
            design = ParameterStorage.get_active_document()
            if not design:
                log_error("No active document for time data load")
                self.send_response(args, {
                    "success": False,
                    "message": "No active document"
                })
                return
                
            # Debug available parameters
            params = design.userParameters
            log_info(f"Found {params.count} total parameters")
            
            # List all parameters for debugging
            param_names = []
            for i in range(params.count):
                param = params.item(i)
                param_names.append(f"{param.name} ({param.value})")
            log_info(f"Parameters: {', '.join(param_names)}")
            
            # Get time parameters names
            time_params = []
            for i in range(params.count):
                param = params.item(i)
                if param.name == ParameterStorage.TIME_DATA_PARAM or param.name.startswith(ParameterStorage.TIME_PREFIX):
                    time_params.append(param.name)
            
            if time_params:
                log_info(f"Found time parameters: {', '.join(time_params)}")
                
                # Retrieve time data 
                log_info("Retrieving time data from parameters")
                time_data = ParameterStorage.retrieve_time_data()
                
                # Very important - ensure we have a valid structure to return, never return None
                if not time_data or not isinstance(time_data, dict):
                    log_warning("Invalid data structure returned from retrieve_time_data, creating empty structure")
                    time_data = {"timeTracker": {"sessions": []}}
                
                # Ensure timeTracker key exists
                if 'timeTracker' not in time_data:
                    log_warning("No timeTracker key in data, adding empty structure")
                    time_data['timeTracker'] = {"sessions": []}
                
                # Ensure sessions key exists
                if 'sessions' not in time_data['timeTracker']:
                    log_warning("No sessions key in timeTracker data, adding empty array")
                    time_data['timeTracker']['sessions'] = []
                
                # Log what we're actually returning
                session_count = len(time_data['timeTracker']['sessions'])
                log_info(f"Returning time data with {session_count} sessions")
                
                # Print detailed info about the time data
                for i, session in enumerate(time_data['timeTracker']['sessions']):
                    log_info(f"Session {i+1}: Date: {session.get('date', 'unknown')}, Times count: {len(session.get('times', []))}")
                    if 'times' in session and len(session['times']) > 0:
                        log_debug(f"  First time value: {session['times'][0]} seconds")
                
                # Debug the final response
                result_json = json.dumps(time_data)
                log_debug(f"Sending response JSON (length: {len(result_json)})")
                log_debug(f"First 100 chars: {result_json[:100]}...")
                
                # Send the actual data back to the palette
                log_info("Sending time data to palette")
                
                # IMPORTANT: Try the standard approach first
                success = self.send_response(args, time_data)
                log_info(f"Parameter data sent successfully: {success}")
                
                # IMPORTANT: NEW APPROACH - Direct DOM manipulation as a fallback mechanism
                # If the palette has our HTML loaded, directly set the data via DOM
                try:
                    log_info("Attempting direct DOM manipulation as fallback...")
                    
                    # Get the data as a JSON string
                    data_json = json.dumps(time_data)
                    
                    # Create JavaScript code to set the hidden input's value and trigger change
                    js_code = f"""
                    try {{
                        console.log("Injected time data via DOM");
                        var dataReceiver = document.getElementById('debugDataReceiver');
                        if (dataReceiver) {{
                            dataReceiver.value = {json.dumps(data_json)};
                            
                            // Create and dispatch a change event
                            var event = new Event('change');
                            dataReceiver.dispatchEvent(event);
                            
                            // Also try direct function call
                            if (window.receiveDirectData) {{
                                window.receiveDirectData({json.dumps(data_json)});
                            }}
                            
                            console.log("DOM data injection complete");
                        }} else {{
                            console.error("debugDataReceiver element not found");
                        }}
                    }} catch(e) {{
                        console.error("DOM injection error:", e);
                    }}
                    """
                    
                    # Execute the JavaScript in the palette
                    if self.window.palette:
                        log_info("Executing DOM injection JavaScript")
                        self.window.palette.executeScript(js_code)
                        log_info("DOM injection complete")
                    else:
                        log_warning("No palette available for DOM injection")
                except Exception as dom_err:
                    log_warning(f"DOM manipulation fallback failed: {str(dom_err)}")
                    # This is just a fallback, so continue even if it fails
                    
            else:
                log_warning("No time parameters found in document")
                empty_data = {"timeTracker": {"sessions": []}}
                self.send_response(args, empty_data)
            
            log_info("=== END LOAD TIME DATA REQUEST ===\n")
                
        except Exception as e:
            log_error(f"Load time data error: {str(e)}")
            log_debug(f"Traceback: {traceback.format_exc()}")
            # Return empty data structure instead of error to avoid UI issues
            empty_data = {"timeTracker": {"sessions": []}}
            self.send_response(args, empty_data)
            log_info("=== END LOAD TIME DATA REQUEST (WITH ERROR) ===\n")
    
    def handle_save_time_data(self, args):
        """Handle saving time data."""
        try:
            log_info("Saving time data to parameters")
            
            if not args.data:
                log_warning("No data provided in save request")
                self.send_response(args, {
                    "success": False,
                    "message": "No data provided"
                })
                return
            
            # Parse the incoming data
            try:
                data = json.loads(args.data)
                time_data = data.get('data', {})
                session_count = len(time_data.get('timeTracker', {}).get('sessions', []))
                log_info(f"Received time data for saving: {session_count} sessions")
                log_debug(f"First part of data: {str(time_data)[:100]}...")
            except json.JSONDecodeError as e:
                log_error(f"JSON parsing error: {e}")
                log_debug(f"Raw data: {args.data[:100]}...")
                self.send_response(args, {
                    "success": False,
                    "message": f"Invalid JSON data: {str(e)}"
                })
                return
                
            # Save to parameters
            success = ParameterStorage.store_time_data(time_data)
            
            log_info(f"Save result: {'success' if success else 'FAILED'}")
            self.send_response(args, {"success": success})
            
        except Exception as e:
            log_error(f"Save time data error: {str(e)}")
            log_debug(f"Traceback: {traceback.format_exc()}")
            self.send_response(args, {
                "success": False,
                "message": f"Error saving time data: {str(e)}"
            })
    
    def handle_project_info(self, args):
        """Handle project info requests."""
        try:
            log_info("Getting project info")
            project_info = self.window.get_project_info()
            log_debug(f"Project info: {project_info}")
            self.send_response(args, project_info)
        except Exception as e:
            log_error(f"Project info error: {str(e)}")
            log_debug(f"Traceback: {traceback.format_exc()}")
            self.send_response(args, {
                "success": False,
                "message": f"Error getting project info: {str(e)}"
            })

    def handle_raw_parameters(self, args):
        """Handle returning raw parameter data for debugging."""
        try:
            design = ParameterStorage.get_active_document()
            if not design:
                log_warning("No active document for raw parameters request")
                self.send_response(args, {
                    "success": False,
                    "message": "No active document"
                })
                return
                
            # Get parameters collection
            params = design.userParameters
            log_info(f"Reading raw data from {params.count} parameters")
            
            # Collect raw parameter data
            raw_params = []
            for i in range(params.count):
                param = params.item(i)
                try:
                    # Get all available information about the parameter
                    param_data = {
                        "name": param.name,
                        "rawExpression": param.expression,
                        "comment": param.comment,
                        "unit": param.unit
                    }
                    
                    # Try to get the value safely
                    try:
                        param_data["value"] = str(param.value)
                    except:
                        param_data["value"] = "Error getting value"
                        
                    raw_params.append(param_data)
                    log_debug(f"Parameter {param.name}: Expression = '{param.expression}', Comment = '{param.comment}'")
                except Exception as param_err:
                    log_error(f"Error getting parameter {i}: {str(param_err)}")
                    raw_params.append({
                        "name": f"Error at index {i}",
                        "error": str(param_err)
                    })
            
            # Return raw data
            self.send_response(args, {
                "success": True,
                "parameterCount": params.count,
                "rawParameters": raw_params
            })
            log_info(f"Returned raw data for {len(raw_params)} parameters")
                
        except Exception as e:
            log_error(f"Raw parameters error: {str(e)}")
            log_debug(f"Traceback: {traceback.format_exc()}")
            self.send_response(args, {
                "success": False,
                "message": f"Error getting raw parameters: {str(e)}"
            })

class TimeTrackerWindow:
    def __init__(self, time_tracker):
        self.app = adsk.core.Application.get()
        self.ui = self.app.userInterface
        self.time_tracker = time_tracker
        self.palette = None
        self.closed_handler = None
        self.html_handler = None

    def show(self):
        try:
            palette_id = 'TimeTrackerPalette'
            palette_name = 'Time Tracker'
            # Use a relative path from the add-in root, as per Fusion 360 docs
            html_path = 'commands/timeTracker/resources/TimeTrackerPalette.html'
            self.palette = self.ui.palettes.itemById(palette_id)
            
            log_info(f"Showing TimeTracker palette - exists: {self.palette is not None}")
            
            if not self.palette:
                log_info("Creating new TimeTracker palette")
                self.palette = self.ui.palettes.add(
                    palette_id,
                    palette_name,
                    html_path,
                    True,  # isVisible
                    True,  # showCloseButton
                    True,  # isResizable
                    420,   # width
                    700    # height
                )
                
                # Set additional options
                self.palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateRight
                self.palette.dockingOption = adsk.core.PaletteDockingOptions.PaletteDockOptionsToVerticalOnly
                
                log_info("TimeTracker palette created successfully")
            else:
                log_info("Using existing TimeTracker palette")
            
            # Clear any existing handlers to avoid duplicates
            if self.palette:
                try:
                    # Remove existing handlers if they exist
                    if hasattr(self.palette, 'closed') and self.closed_handler:
                        self.palette.closed.remove(self.closed_handler)
                    if hasattr(self.palette, 'incomingFromHTML') and self.html_handler:
                        self.palette.incomingFromHTML.remove(self.html_handler)
                except:
                    log_warning("Failed to remove existing handlers - continuing anyway")
                
            # Always set up handlers when showing the palette
            # This ensures the palette can receive events even if it's being reused
            self.closed_handler = PaletteClosedHandler(self)
            self.palette.closed.add(self.closed_handler)
            
            # Add HTML event handler
            self.html_handler = PaletteHTMLEventHandler(self)
            self.palette.incomingFromHTML.add(self.html_handler)
            
            # Make palette visible
            self.palette.isVisible = True
            log_info("TimeTracker palette set to visible")
        except Exception as e:
            log_error(f"Failed to show window: {str(e)}")
            log_debug(f"Traceback: {traceback.format_exc()}")
            if self.ui:
                self.ui.messageBox('Failed to show window:\n{}'.format(traceback.format_exc()))
    
    def get_project_info(self):
        """Get information about the current Fusion 360 project."""
        try:
            # Get active document
            doc = self.app.activeDocument
            if not doc:
                log_warning("No active document for project info")
                return {"name": "No active document", "id": ""}
            
            # Get document name and ID
            info = {
                "name": doc.name,
                "id": doc.dataFile.id if doc.dataFile else "",
                "path": doc.dataFile.fullPath if doc.dataFile else ""
            }
            log_debug(f"Project info retrieved: {info}")
            return info
        except Exception as e:
            log_error(f"Error getting project info: {str(e)}")
            return {"name": "Error getting project info", "id": ""} 