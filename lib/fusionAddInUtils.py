import adsk.core
import adsk.fusion
import traceback
import datetime
import os

# Global variables
handlers = []
_debug_mode = True  # Set to False in production to reduce log output

# Log file path (in the same directory as the add-in)
log_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'timekeeper_debug.log')

def handle_error(name):
    """Show error message and log the error"""
    error_message = 'Failed to {}:\n{}'.format(name, traceback.format_exc())
    log_error(error_message)
    
    if adsk.core.Application.get():
        adsk.core.Application.get().userInterface.messageBox(error_message)

def clear_handlers():
    global handlers
    for handler in handlers:
        handler.dispose()
    handlers = []

def get_timestamp():
    """Get current timestamp for logging"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def log_to_text_window(message, level="INFO"):
    """
    Log a message to Fusion 360's Text Commands window
    
    Args:
        message (str): The message to log
        level (str): Log level (INFO, WARNING, ERROR, DEBUG)
    """
    timestamp = get_timestamp()
    formatted_message = f"[{timestamp}] [{level}] {message}"
    
    # Log to file for persistent debugging
    log_to_file(formatted_message)
    
    # Only show DEBUG messages in debug mode
    if level == "DEBUG" and not _debug_mode:
        return
        
    app = adsk.core.Application.get()
    if app:
        text_palette = app.userInterface.palettes.itemById('TextCommands')
        if text_palette:
            text_palette.writeText(formatted_message)
        else:
            print(f"TextCommands palette not available: {formatted_message}")
    else:
        print(f"Application not available: {formatted_message}")

def log_to_file(message):
    """Log message to a file for persistent debugging"""
    try:
        with open(log_file_path, 'a') as f:
            f.write(f"{message}\n")
    except Exception:
        pass  # Fail silently if file logging doesn't work

def log_debug(message):
    """Log debug message"""
    if _debug_mode:
        log_to_text_window(message, "DEBUG")

def log_info(message):
    """Log info message"""
    log_to_text_window(message, "INFO")

def log_warning(message):
    """Log warning message"""
    log_to_text_window(message, "WARNING")

def log_error(message):
    """Log error message"""
    log_to_text_window(message, "ERROR")

def enable_debug_mode(enabled=True):
    """Enable or disable debug mode"""
    global _debug_mode
    _debug_mode = enabled
    log_info(f"Debug mode {'enabled' if enabled else 'disabled'}")

def log_parameter_detail(param):
    """Log detailed information about a parameter"""
    try:
        log_debug(f"Parameter: {param.name}")
        log_debug(f"  - Expression: {param.expression}")
        log_debug(f"  - Value: {param.value}")
        log_debug(f"  - Comment: {param.comment}")
        log_debug(f"  - Unit: {param.unit}")
    except Exception as e:
        log_error(f"Error logging parameter detail: {str(e)}") 