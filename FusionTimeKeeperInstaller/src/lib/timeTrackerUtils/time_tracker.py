import os
import json
from datetime import datetime
from .parameter_storage import ParameterStorage

class TimeTracker:
    def __init__(self):
        self.current_session = None
        self.sessions = []
        # Keep the data_file path for backward compatibility
        self.data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'sessions.json')
        self._load_sessions()

    def _load_sessions(self):
        try:
            # First try to load from parameters
            param_data = ParameterStorage.retrieve_time_data()
            if param_data and 'timeTracker' in param_data:
                data = param_data['timeTracker']
                if 'sessions' in data:
                    loaded_sessions = data.get('sessions', [])
                    # Validate and convert the session format if needed
                    self.sessions = self._ensure_compatible_session_format(loaded_sessions)
                    return
            
            # Fall back to file-based loading if parameters didn't work
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.sessions = json.load(f)
        except Exception as e:
            print(f"Error loading sessions: {str(e)}")
            self.sessions = []

    def _ensure_compatible_session_format(self, sessions):
        """
        Ensures that loaded sessions match the expected format.
        Converts simplified formats (like {date, times} from sequential parameters)
        to the full format expected by the HTML palette.
        """
        try:
            compatible_sessions = []
            for session in sessions:
                # Check if this is using the simplified format with just 'date' and 'times'
                if 'date' in session and 'times' in session and 'id' not in session:
                    # This is from sequential parameters - convert each time entry to a full session
                    date = session['date']
                    for i, duration in enumerate(session['times']):
                        # Create a compatible session record
                        compatible_sessions.append({
                            'id': len(compatible_sessions) + 1,
                            'date': date,
                            'start_time': datetime.now().isoformat(),  # We don't have the actual time
                            'end_time': datetime.now().isoformat(),    # We don't have the actual time
                            'duration': duration,
                            'project_path': 'Unknown',  # We don't have the project path
                            'notes': f'Imported from sequential parameter {i+1}'
                        })
                else:
                    # This is already in the expected format or close enough
                    if 'id' not in session:
                        session['id'] = len(compatible_sessions) + 1
                    compatible_sessions.append(session)
                    
            return compatible_sessions
        except Exception as e:
            print(f"Error converting session format: {str(e)}")
            return sessions  # Return original on error

    def _save_sessions(self):
        try:
            # First try to save to parameters
            success = ParameterStorage.store_time_data({
                'timeTracker': {
                    'sessions': self.sessions
                }
            })
            
            if not success:
                # Fall back to file-based storage
                os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
                with open(self.data_file, 'w') as f:
                    json.dump(self.sessions, f)
                    
            return success
        except Exception as e:
            print(f"Error saving sessions: {str(e)}")
            return False

    def start_timer(self, project_path):
        """Start a new timing session for the given project."""
        if not self.current_session:
            # Make sure we have the latest data before starting a new session
            self._load_sessions()
            
            # Create a new session with a unique ID
            session_id = self._generate_session_id()
            
            self.current_session = {
                'id': session_id,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'duration': None,
                'project_path': project_path,
                'notes': ''
            }
            
            # Add to sessions list
            self.sessions.append(self.current_session)
            
            # Save immediately to ensure it's stored
            self._save_sessions()
            return True
        
        return False  # Session already running

    def stop_timer(self):
        """Stop the current timing session and save the duration."""
        if self.current_session:
            # Calculate end time and duration
            end_time = datetime.now()
            start_time = datetime.fromisoformat(self.current_session['start_time'])
            duration = (end_time - start_time).total_seconds()
            
            # Update the current session with end time and duration
            self.current_session['end_time'] = end_time.isoformat()
            self.current_session['duration'] = duration
            
            # Instead of modifying the session in place, find and replace it in the sessions list
            # This ensures we update the correct session even if the list was reloaded
            for i, session in enumerate(self.sessions):
                if session.get('id') == self.current_session['id']:
                    self.sessions[i] = self.current_session
                    break
            
            # Save the updated sessions
            success = self._save_sessions()
            
            # Clear the current session
            self.current_session = None
            
            return success
        
        return False  # No active session

    def _generate_session_id(self):
        """Generate a unique session ID."""
        # Get the highest existing ID
        max_id = 0
        for session in self.sessions:
            if 'id' in session and session['id'] > max_id:
                max_id = session['id']
        
        # Return the next ID in sequence
        return max_id + 1

    def get_current_session_duration(self):
        """Get the duration of the current session in seconds."""
        if self.current_session:
            start_time = datetime.fromisoformat(self.current_session['start_time'])
            duration = (datetime.now() - start_time).total_seconds()
            return duration
        return 0

    def get_total_time(self):
        """Get the total time tracked across all sessions in seconds."""
        total = 0
        
        # Ensure we have the latest data
        self._load_sessions()
        
        # Sum all session durations
        for session in self.sessions:
            if 'duration' in session and session['duration']:
                total += session['duration']
            # Also include current session if it's not already counted
            elif self.current_session and session.get('id') == self.current_session.get('id'):
                total += self.get_current_session_duration()
        
        return total

    def get_session_history(self):
        """Get the list of all session records."""
        # Ensure we have the latest data
        self._load_sessions()
        return self.sessions

    def export_to_csv(self, file_path):
        """Export the session history to a CSV file."""
        try:
            import pandas as pd
            
            # Ensure we have the latest data
            self._load_sessions()
            
            # Format data for export
            export_data = []
            for session in self.sessions:
                # Extract date, start time, end time, duration and notes
                export_data.append({
                    'Date': session.get('date', ''),
                    'Start Time': session.get('start_time', ''),
                    'End Time': session.get('end_time', ''),
                    'Duration (seconds)': session.get('duration', 0),
                    'Project': session.get('project_path', ''),
                    'Notes': session.get('notes', '')
                })
            
            # Create dataframe and export to CSV
            df = pd.DataFrame(export_data)
            df.to_csv(file_path, index=False)
            
            return True
        except Exception as e:
            print(f"Error exporting to CSV: {str(e)}")
            return False 