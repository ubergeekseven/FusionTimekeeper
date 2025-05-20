from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                             QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon
import os
from datetime import datetime, timedelta

class TimeTrackerWindow(QMainWindow):
    def __init__(self, time_tracker):
        super().__init__()
        self.time_tracker = time_tracker
        self.setup_ui()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_current_time)
        self.update_timer.start(1000)  # Update every second

    def setup_ui(self):
        self.setWindowTitle("Fusion Timekeeper")
        self.setMinimumSize(600, 400)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Current time display
        self.time_label = QLabel("00:00:00")
        self.time_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)

        # Start/Stop button
        self.timer_button = QPushButton("Start Timer")
        self.timer_button.setFont(QFont("Arial", 12))
        self.timer_button.clicked.connect(self.toggle_timer)
        layout.addWidget(self.timer_button)

        # Total time display
        self.total_time_label = QLabel("Total Time: 00:00:00")
        self.total_time_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.total_time_label)

        # Session history table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Start Time", "End Time", "Duration", "Notes"])
        layout.addWidget(self.history_table)

        # Export buttons
        button_layout = QHBoxLayout()
        export_csv_btn = QPushButton("Export to CSV")
        export_csv_btn.clicked.connect(self.export_to_csv)
        export_txt_btn = QPushButton("Export to Text")
        export_txt_btn.clicked.connect(self.export_to_text)
        button_layout.addWidget(export_csv_btn)
        button_layout.addWidget(export_txt_btn)
        layout.addLayout(button_layout)

        self.update_history_table()

    def toggle_timer(self):
        if self.time_tracker.current_session:
            self.time_tracker.stop_timer()
            self.timer_button.setText("Start Timer")
            self.update_history_table()
        else:
            # Get the current project path from Fusion 360
            project_path = self.get_current_project_path()
            if project_path:
                self.time_tracker.start_timer(project_path)
                self.timer_button.setText("Stop Timer")

    def update_current_time(self):
        if self.time_tracker.current_session:
            duration = self.time_tracker.get_current_session_duration()
            self.time_label.setText(str(duration).split('.')[0])
        else:
            self.time_label.setText("00:00:00")

        total_time = self.time_tracker.get_total_time()
        self.total_time_label.setText(f"Total Time: {str(total_time).split('.')[0]}")

    def update_history_table(self):
        sessions = self.time_tracker.get_session_history()
        self.history_table.setRowCount(len(sessions))
        
        for row, session in enumerate(sessions):
            start_time = datetime.fromisoformat(session[1])
            end_time = datetime.fromisoformat(session[2]) if session[2] else None
            duration = timedelta(seconds=session[3]) if session[3] else None
            
            self.history_table.setItem(row, 0, QTableWidgetItem(start_time.strftime("%Y-%m-%d %H:%M:%S")))
            self.history_table.setItem(row, 1, QTableWidgetItem(end_time.strftime("%Y-%m-%d %H:%M:%S") if end_time else "In Progress"))
            self.history_table.setItem(row, 2, QTableWidgetItem(str(duration).split('.')[0] if duration else "In Progress"))
            self.history_table.setItem(row, 3, QTableWidgetItem(session[4] or ""))

    def export_to_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to CSV", "", "CSV Files (*.csv)"
        )
        if file_path:
            try:
                self.time_tracker.export_to_csv(file_path)
                QMessageBox.information(self, "Success", "Data exported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export data: {str(e)}")

    def export_to_text(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to Text", "", "Text Files (*.txt)"
        )
        if file_path:
            try:
                sessions = self.time_tracker.get_session_history()
                with open(file_path, 'w') as f:
                    f.write("Fusion Timekeeper Session History\n")
                    f.write("=" * 50 + "\n\n")
                    for session in sessions:
                        start_time = datetime.fromisoformat(session[1])
                        end_time = datetime.fromisoformat(session[2]) if session[2] else None
                        duration = timedelta(seconds=session[3]) if session[3] else None
                        
                        f.write(f"Session {session[0]}\n")
                        f.write(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S') if end_time else 'In Progress'}\n")
                        f.write(f"Duration: {str(duration).split('.')[0] if duration else 'In Progress'}\n")
                        if session[4]:
                            f.write(f"Notes: {session[4]}\n")
                        f.write("\n")
                
                QMessageBox.information(self, "Success", "Data exported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export data: {str(e)}")

    def get_current_project_path(self):
        # This method should be implemented to get the current project path from Fusion 360
        # For now, we'll return a placeholder
        return "current_project.f3d" 