import adsk.core
import adsk.fusion
import json
import traceback
import datetime
import sys
import os

# Add the lib directory to path if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.abspath(os.path.join(current_dir, '..'))
if lib_dir not in sys.path:
    sys.path.append(lib_dir)

# Use absolute import
from fusionAddInUtils import log_info, log_debug, log_warning, log_error, log_parameter_detail

class ParameterStorage:
    """
    Utility class for storing and retrieving data using Fusion 360 document parameters.
    This allows data to be saved with the document and persist across sessions.
    """
    
    # Parameter group and names
    PARAM_GROUP = 'FusionTimekeeper'
    TIME_DATA_PARAM = 'TimeData'
    NOTES_DATA_PARAM = 'NotesData'
    TIME_PREFIX = 'Time'
    NOTE_PREFIX = 'Note'
    
    @staticmethod
    def get_active_document():
        """Get the active Fusion 360 document."""
        app = adsk.core.Application.get()
        if not app:
            log_error("CRITICAL ERROR: No application instance found")
            return None
        
        try:
            # Get active document with proper error handling
            doc = app.activeDocument
            if not doc:
                log_warning("No active document found - this is normal during initial load")
                return None
                
            # Get the design
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            if not design:
                log_error("No design found in active document")
                return None
                
            log_info(f"Active document found: {doc.name}")
            return design
            
        except RuntimeError as e:
            # Handle the specific InternalValidationError that occurs during initial load
            if "InternalValidationError" in str(e):
                log_warning("Runtime validation error while accessing activeDocument - this is normal during initial load")
            else:
                log_error(f"RuntimeError in get_active_document: {str(e)}")
            return None
        except Exception as e:
            log_error(f"Error in get_active_document: {str(e)}")
            log_debug(f"Traceback: {traceback.format_exc()}")
            return None
    
    @staticmethod
    def store_time_data(data):
        """Store time tracking data in document parameters."""
        try:
            log_info("\n=== PARAMETER STORAGE DEBUG ===")
            log_info("Attempting to store time data in parameters")
            design = ParameterStorage.get_active_document()
            if not design:
                log_error("CRITICAL ERROR: Failed to get active document")
                return False
                
            # Convert data to JSON string
            json_data = json.dumps(data)
            log_debug(f"Time data JSON length: {len(json_data)}")
            log_debug(f"First 100 chars: {json_data[:100]}")
            
            # Safety check - if the JSON data is too large, we should prioritize sequential storage
            large_data = len(json_data) > 2000  # Fusion has limits on string parameter length
            if large_data:
                log_warning("Warning: Time data is large, may not fit in a single parameter")
                log_info("Using sequential parameter storage as primary method")
                
                # For large data, try sequential storage first
                success = False
                try:
                    log_info("\nStoring sequential parameters...")
                    success = ParameterStorage.store_time_data_sequential(data)
                    if success:
                        log_info("Sequential parameters created successfully")
                        # Return early as we're using sequential params as primary storage
                        log_info("=== END PARAMETER STORAGE DEBUG ===\n")
                        return True
                    else:
                        log_warning("Failed to create sequential parameters")
                except Exception as seq_e:
                    log_error(f"Sequential parameter error: {str(seq_e)}")
                    log_debug(f"Sequential parameter error traceback: {traceback.format_exc()}")
                    
                # If sequential failed, we'll still try the JSON method below
            
            # Get parameters collection and check if parameter exists
            log_info("\nChecking user parameters...")
            params = design.userParameters
            log_debug(f"Parameter count: {params.count}")
            
            # Clean up the JSON string to create a valid parameter expression
            # First, ensure all double quotes are properly escaped for the parameter expression
            param_expression = json_data.replace('"', '\\"')
            
            try:
                # Try to create/update the TimeData parameter
                param = params.itemByName(ParameterStorage.TIME_DATA_PARAM)
                
                if param:
                    log_info(f"Updating existing parameter: {ParameterStorage.TIME_DATA_PARAM}")
                    log_parameter_detail(param)
                    
                    # Use a properly formatted string expression with quotes
                    try:
                        param.expression = f'"{param_expression}"'
                        log_info("Parameter expression updated")
                    except Exception as expr_error:
                        log_error(f"Error updating parameter expression: {str(expr_error)}")
                        log_debug(f"Expression error traceback: {traceback.format_exc()}")
                        # If we failed due to size, but sequential storage worked, consider it a success
                        if large_data:
                            log_warning("Falling back to sequential storage only")
                            # Try sequential storage again if we haven't already
                            success = ParameterStorage.store_time_data_sequential(data)
                            return success
                        return False
                else:
                    log_info(f"Creating new parameter: {ParameterStorage.TIME_DATA_PARAM}")
                    try:
                        # When creating a new parameter, we need to wrap the string in quotes
                        new_param = params.add(
                            ParameterStorage.TIME_DATA_PARAM,
                            adsk.core.ValueInput.createByString(f'"{param_expression}"'),
                            '',  # unit type (empty for text)
                            ParameterStorage.PARAM_GROUP
                        )
                        if new_param:
                            log_info("Parameter created successfully")
                            log_parameter_detail(new_param)
                        else:
                            log_warning("Failed to create parameter - no error but null returned")
                    except Exception as create_error:
                        log_error(f"Error creating parameter: {str(create_error)}")
                        log_debug(f"Creation error traceback: {traceback.format_exc()}")
                        # If we failed due to size, but sequential storage worked, consider it a success
                        if large_data:
                            log_warning("Falling back to sequential storage only")
                            # Try sequential storage again if we haven't already
                            success = ParameterStorage.store_time_data_sequential(data)
                            return success
                        return False
                
                # Always store using the sequential parameter approach as backup
                if not large_data:  # Skip if we already did this for large data
                    try:
                        log_info("\nStoring sequential parameters...")
                        success = ParameterStorage.store_time_data_sequential(data)
                        if success:
                            log_info("Sequential parameters created successfully")
                        else:
                            log_warning("Failed to create sequential parameters")
                    except Exception as seq_e:
                        log_error(f"Sequential parameter error: {str(seq_e)}")
                        log_debug(f"Sequential parameter error traceback: {traceback.format_exc()}")
                
                log_info("Time data stored successfully")
                log_info("=== END PARAMETER STORAGE DEBUG ===\n")
                return True
            except Exception as inner_e:
                log_error(f"ERROR in parameter creation/update: {str(inner_e)}")
                log_debug(f"Inner Exception: {traceback.format_exc()}")
                return False
        except Exception as e:
            log_error(f"CRITICAL ERROR: Failed to store time data: {str(e)}")
            log_debug(f"Traceback: {traceback.format_exc()}")
            return False
    
    @staticmethod
    def store_time_data_sequential(data):
        """
        Store time data using sequential parameters (Time1, Time2, etc.)
        Each parameter stores seconds as value and date info in comments
        """
        try:
            design = ParameterStorage.get_active_document()
            if not design:
                return False
                
            # Get user parameters
            params = design.userParameters
            
            # First, delete any existing Time parameters
            time_params = []
            for i in range(params.count):
                param = params.item(i)
                if param.name.startswith(ParameterStorage.TIME_PREFIX):
                    time_params.append(param)
            
            log_debug(f"Found {len(time_params)} existing time parameters to delete")
            
            # Delete in reverse order to avoid index issues
            for param in reversed(time_params):
                param_name = param.name
                try:
                    param.deleteMe()
                    log_debug(f"Deleted parameter {param_name}")
                except Exception as delete_err:
                    log_error(f"Error deleting parameter {param_name}: {str(delete_err)}")
                
            # Now create new parameters for each time entry
            timeTracker = data.get('timeTracker', {})
            sessions = timeTracker.get('sessions', [])
            
            log_debug(f"Creating parameters for {len(sessions)} sessions")
            
            # Create time parameters
            param_index = 1
            for session in sessions:
                date = session.get('date', '')
                times = session.get('times', [])
                
                log_debug(f"Session {date} has {len(times)} time entries")
                
                for time_value in times:
                    param_name = f"{ParameterStorage.TIME_PREFIX}{param_index}"
                    try:
                        params.add(
                            param_name,
                            adsk.core.ValueInput.createByReal(time_value),
                            's',  # seconds
                            f"Time entry on {date}"
                        )
                        param_index += 1
                    except Exception as create_err:
                        log_error(f"Error creating parameter {param_name}: {str(create_err)}")
            
            log_info(f"Created {param_index-1} sequential time parameters")
            return True
        except Exception as e:
            log_error(f"Failed to store sequential time data: {str(e)}")
            log_debug(f"Traceback: {traceback.format_exc()}")
            return False
    
    @staticmethod
    def retrieve_time_data():
        """Retrieve time tracking data from document parameters."""
        try:
            log_info("\n=== PARAMETER RETRIEVAL DEBUG ===")
            log_info("Attempting to retrieve time data from parameters")
            design = ParameterStorage.get_active_document()
            if not design:
                log_warning("No active document available - returning empty data structure")
                log_info("=== END PARAMETER RETRIEVAL DEBUG ===\n")
                return {"timeTracker": {"sessions": []}}
                
            # Debug parameter count
            params = design.userParameters
            log_info(f"Found {params.count} total user parameters")
            
            # List all parameter names for debugging
            param_names = []
            for i in range(params.count):
                param = params.item(i)
                param_names.append(f"{param.name} ({param.value})")
            log_info(f"Parameter names: {', '.join(param_names)}")
            
            # First try to get from the JSON parameter
            param = params.itemByName(ParameterStorage.TIME_DATA_PARAM)
            
            if param:
                log_info(f"Found main TimeData parameter")
                log_parameter_detail(param)
                
                # Get JSON string from parameter expression
                json_str = param.expression
                
                # Log the raw expression
                log_debug(f"Raw parameter expression: {json_str[:30]}...")
                
                # Remove surrounding quotes if present
                if json_str.startswith('"') and json_str.endswith('"'):
                    json_str = json_str[1:-1]
                    log_debug("Removed surrounding quotes")
                    
                # Handle escaped quotes if present
                json_str = json_str.replace('\\"', '"')
                log_debug("Replaced escaped quotes")
                
                log_debug(f"Processed JSON string, length: {len(json_str)}")
                log_debug(f"First 30 chars: {json_str[:30]}...")
                
                # Parse JSON data
                try:
                    data = json.loads(json_str)
                    log_info("Time data parsed successfully")
                    
                    # Debug the data structure
                    sessions = data.get('timeTracker', {}).get('sessions', [])
                    session_count = len(sessions)
                    log_info(f"Retrieved {session_count} sessions from TimeData parameter")
                    
                    if session_count > 0:
                        # Log first session details
                        first_session = sessions[0]
                        log_info(f"First session - Date: {first_session.get('date', 'unknown')}, Times count: {len(first_session.get('times', []))}")
                    
                    log_info("=== END PARAMETER RETRIEVAL DEBUG ===\n")
                    return data
                except json.JSONDecodeError as je:
                    log_error(f"JSON parse error: {je}")
                    log_debug(f"Error at position {je.pos}: {json_str[max(0, je.pos-10):min(len(json_str), je.pos+10)]}")
                    
                    # Try to reconstruct from sequential parameters
                    log_info("Attempting to reconstruct from sequential parameters")
                    data = ParameterStorage.retrieve_time_data_sequential()
                    log_info("=== END PARAMETER RETRIEVAL DEBUG ===\n")
                    return data
            else:
                log_info("TimeData parameter not found, trying sequential parameters")
                # Try to reconstruct from sequential parameters
                data = ParameterStorage.retrieve_time_data_sequential()
                
                # Verify the data structure
                if data and 'timeTracker' in data and 'sessions' in data['timeTracker']:
                    session_count = len(data['timeTracker']['sessions'])
                    log_info(f"Retrieved {session_count} sessions from sequential parameters")
                    
                    # Additional verification and cleanup
                    sessions = data['timeTracker']['sessions']
                    if session_count > 0:
                        # Ensure the format of the first session is correct
                        first_session = sessions[0]
                        if 'date' not in first_session:
                            log_warning("Missing date field in first session, might be data format issue")
                        if 'times' in first_session:
                            log_info(f"First session has {len(first_session['times'])} time entries")
                else:
                    log_warning("No valid data structure from sequential parameters")
                    
                log_info("=== END PARAMETER RETRIEVAL DEBUG ===\n")
                return data
        except Exception as e:
            log_error(f"Failed to retrieve time data: {str(e)}")
            log_debug(f"Traceback: {traceback.format_exc()}")
            log_info("=== END PARAMETER RETRIEVAL DEBUG ===\n")
            return {"timeTracker": {"sessions": []}}
    
    @staticmethod
    def retrieve_time_data_sequential():
        """
        Reconstruct time data from sequential parameters (Time1, Time2, etc.)
        """
        try:
            design = ParameterStorage.get_active_document()
            if not design:
                log_warning("No active document available for sequential parameter retrieval")
                return {"timeTracker": {"sessions": []}}
                
            params = design.userParameters
            
            # Find all Time parameters
            time_params = []
            for i in range(params.count):
                param = params.item(i)
                if param.name.startswith(ParameterStorage.TIME_PREFIX):
                    time_params.append(param)
            
            log_debug(f"Found {len(time_params)} sequential time parameters")
            
            if not time_params:
                log_warning("No time parameters found in document")
                return {"timeTracker": {"sessions": []}}
            
            # Sort by parameter number - IMPROVED SORTING
            def get_param_number(param):
                try:
                    return int(param.name[len(ParameterStorage.TIME_PREFIX):])
                except ValueError:
                    return 9999  # Default high value for invalid formats
                    
            time_params.sort(key=get_param_number)
            
            # Log the sorted parameters for debugging
            sorted_params = [f"{p.name}={p.value}" for p in time_params[:5]]
            log_debug(f"First few sorted parameters: {', '.join(sorted_params)}")
            
            # Reconstruct sessions by date
            sessions_by_date = {}
            for param in time_params:
                # Extract date from comment
                comment = param.comment
                date = "Unknown"
                if "Time entry on " in comment:
                    date = comment.replace("Time entry on ", "").strip()
                
                # Get time value in seconds
                seconds = param.value
                log_debug(f"Parameter {param.name}: {seconds}s on {date}")
                
                # Add to sessions by date
                if date not in sessions_by_date:
                    sessions_by_date[date] = []
                sessions_by_date[date].append(seconds)
            
            # Convert to sessions array
            sessions = []
            for date, times in sessions_by_date.items():
                sessions.append({
                    "date": date,
                    "times": times
                })
            
            # Sort sessions by date
            sessions.sort(key=lambda s: s["date"])
            
            # Create the full data structure
            data = {
                "timeTracker": {
                    "sessions": sessions
                }
            }
            
            log_info(f"Reconstructed time data from {len(time_params)} sequential parameters")
            log_info(f"Created {len(sessions)} session entries")
            
            # Log detailed session information for debugging
            for i, session in enumerate(sessions):
                log_info(f"Session {i+1}: Date: {session['date']}, Times count: {len(session['times'])}")
                if len(session['times']) > 0:
                    log_debug(f"  First time: {session['times'][0]} seconds")
                    
            # Make sure this is compatible with the TimeTracker.py expectations 
            # and the HTML palette's expected format
            log_debug("Checking for format compatibility with TimeTracker.py")
            
            # Check if this data structure is correct based on TimeTracker.py expectations
            if sessions and len(sessions) > 0:
                # Test accessing a session and time entry
                try:
                    test_session = sessions[0]
                    test_date = test_session.get('date', 'No date')
                    test_times = test_session.get('times', [])
                    test_count = len(test_times)
                    log_debug(f"Format check: First session date: {test_date}, times count: {test_count}")
                    
                    if test_count > 0:
                        log_debug(f"Format check: First time value: {test_times[0]}")
                except Exception as fmt_err:
                    log_error(f"Format compatibility check failed: {str(fmt_err)}")
            
            return data
        except Exception as e:
            log_error(f"Failed to retrieve sequential time data: {str(e)}")
            log_debug(f"Traceback: {traceback.format_exc()}")
            return {"timeTracker": {"sessions": []}}
    
    @staticmethod
    def store_notes_data(notes):
        """Store notes data in document parameters."""
        try:
            log_info("Attempting to store notes data in parameters")
            design = ParameterStorage.get_active_document()
            if not design:
                log_error("Failed to get active document")
                return False
                
            # Convert data to JSON string
            json_data = json.dumps({"notes": notes})
            log_debug(f"Notes JSON length: {len(json_data)}")
            
            # Properly escape quotes for parameter expression
            param_expression = json_data.replace('"', '\\"')
            
            # Get or create the parameter
            params = design.userParameters
            param = params.itemByName(ParameterStorage.NOTES_DATA_PARAM)
            
            if param:
                log_info(f"Updating existing parameter: {ParameterStorage.NOTES_DATA_PARAM}")
                log_parameter_detail(param)
                # Update existing parameter
                param.expression = f'"{param_expression}"'
            else:
                log_info(f"Creating new parameter: {ParameterStorage.NOTES_DATA_PARAM}")
                # Create new parameter
                new_param = params.add(
                    ParameterStorage.NOTES_DATA_PARAM,
                    adsk.core.ValueInput.createByString(f'"{param_expression}"'),
                    '',  # unit type (empty for text)
                    ParameterStorage.PARAM_GROUP
                )
                if new_param:
                    log_parameter_detail(new_param)
            
            # Also store using the sequential parameter approach
            ParameterStorage.store_notes_data_sequential(notes)
            
            log_info("Notes data stored successfully")
            return True
        except Exception as e:
            log_error(f"Failed to store notes data: {str(e)}")
            log_debug(f"Traceback: {traceback.format_exc()}")
            return False
            
    @staticmethod
    def store_notes_data_sequential(notes):
        """
        Store notes using sequential parameters (Note1, Note2, etc.)
        Each parameter stores its index as value and note content in comments
        """
        try:
            design = ParameterStorage.get_active_document()
            if not design:
                return False
                
            # Get user parameters
            params = design.userParameters
            
            # First, delete any existing Note parameters
            note_params = []
            for i in range(params.count):
                param = params.item(i)
                if param.name.startswith(ParameterStorage.NOTE_PREFIX):
                    note_params.append(param)
            
            log_debug(f"Found {len(note_params)} existing note parameters to delete")
            
            # Delete in reverse order to avoid index issues
            for param in reversed(note_params):
                param_name = param.name
                try:
                    param.deleteMe()
                    log_debug(f"Deleted parameter {param_name}")
                except Exception as delete_err:
                    log_error(f"Error deleting parameter {param_name}: {str(delete_err)}")
            
            # If notes is empty, we're done
            if not notes:
                return True
                
            # Split notes into lines
            note_lines = notes.split('\n')
            
            log_debug(f"Creating parameters for {len(note_lines)} note lines")
            
            # Create a parameter for each line
            notes_created = 0
            for i, line in enumerate(note_lines):
                if line.strip():  # Only store non-empty lines
                    param_name = f"{ParameterStorage.NOTE_PREFIX}{i+1}"
                    try:
                        params.add(
                            param_name,
                            adsk.core.ValueInput.createByReal(i+1),  # Index as value
                            '',  # No unit
                            line  # Note content as comment
                        )
                        notes_created += 1
                    except Exception as create_err:
                        log_error(f"Error creating parameter {param_name}: {str(create_err)}")
            
            log_info(f"Created {notes_created} sequential note parameters")
            return True
        except Exception as e:
            log_error(f"Failed to store sequential notes data: {str(e)}")
            log_debug(f"Traceback: {traceback.format_exc()}")
            return False
    
    @staticmethod
    def retrieve_notes_data():
        """Retrieve notes data from document parameters."""
        try:
            log_info("Attempting to retrieve notes data from parameters")
            design = ParameterStorage.get_active_document()
            if not design:
                log_error("Failed to get active document")
                return None
                
            # First try to get from the JSON parameter
            params = design.userParameters
            param = params.itemByName(ParameterStorage.NOTES_DATA_PARAM)
            
            if param:
                log_info(f"Found main NotesData parameter")
                log_parameter_detail(param)
                
                # Get JSON string from parameter expression
                json_str = param.expression
                
                # Remove surrounding quotes if present
                if json_str.startswith('"') and json_str.endswith('"'):
                    json_str = json_str[1:-1]
                    
                # Handle escaped quotes if present
                json_str = json_str.replace('\\"', '"')
                
                log_debug(f"Retrieved notes JSON string, length: {len(json_str)}")
                
                # Parse JSON data
                try:
                    data = json.loads(json_str)
                    log_info("Notes data parsed successfully")
                    return data.get("notes", "")
                except json.JSONDecodeError as je:
                    log_error(f"JSON parse error: {je}")
                    log_debug(f"Error at position {je.pos}: {json_str[max(0, je.pos-10):min(len(json_str), je.pos+10)]}")
                    # Try to reconstruct from sequential parameters
                    return ParameterStorage.retrieve_notes_data_sequential()
            else:
                log_info("NotesData parameter not found, trying sequential parameters")
                # Try to reconstruct from sequential parameters
                return ParameterStorage.retrieve_notes_data_sequential()
        except Exception as e:
            log_error(f"Failed to retrieve notes data: {str(e)}")
            log_debug(f"Traceback: {traceback.format_exc()}")
            return None
            
    @staticmethod
    def retrieve_notes_data_sequential():
        """
        Reconstruct notes from sequential parameters (Note1, Note2, etc.)
        """
        try:
            design = ParameterStorage.get_active_document()
            if not design:
                return None
                
            params = design.userParameters
            
            # Find all Note parameters
            note_params = []
            for i in range(params.count):
                param = params.item(i)
                if param.name.startswith(ParameterStorage.NOTE_PREFIX):
                    note_params.append(param)
            
            log_debug(f"Found {len(note_params)} sequential note parameters")
            
            if not note_params:
                return ""
            
            # Sort by parameter number
            note_params.sort(key=lambda p: int(p.name[len(ParameterStorage.NOTE_PREFIX):]))
            
            # Reconstruct notes from comments
            note_lines = []
            for param in note_params:
                note_lines.append(param.comment)
            
            # Join lines into a single string
            notes = '\n'.join(note_lines)
            
            log_info(f"Reconstructed notes from {len(note_params)} sequential parameters")
            return notes
        except Exception as e:
            log_error(f"Failed to retrieve sequential notes data: {str(e)}")
            log_debug(f"Traceback: {traceback.format_exc()}")
            return None 