"""
Log Viewer Widget - Real-time log monitoring
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QComboBox,
    QPushButton, QLabel, QCheckBox, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QTextCursor, QTextCharFormat
from datetime import datetime
import json


class LogViewerWidget(QWidget):
    """Widget for viewing and filtering logs"""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
        self._setup_log_monitor()
    
    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Control bar
        control_layout = QHBoxLayout()
        
        # Log level filter
        control_layout.addWidget(QLabel("Level:"))
        self.level_filter = QComboBox()
        self.level_filter.addItems(["All", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_filter.currentTextChanged.connect(self._apply_filters)
        control_layout.addWidget(self.level_filter)
        
        # Search box
        control_layout.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search logs...")
        self.search_box.textChanged.connect(self._apply_filters)
        control_layout.addWidget(self.search_box)
        
        # Max logs
        control_layout.addWidget(QLabel("Max Logs:"))
        self.max_logs_spin = QSpinBox()
        self.max_logs_spin.setMinimum(10)
        self.max_logs_spin.setMaximum(10000)
        self.max_logs_spin.setValue(1000)
        control_layout.addWidget(self.max_logs_spin)
        
        # Clear button
        clear_btn = QPushButton("🗑 Clear")
        clear_btn.clicked.connect(self._clear_logs)
        control_layout.addWidget(clear_btn)
        
        # Export button
        export_btn = QPushButton("💾 Export")
        export_btn.clicked.connect(self._export_logs)
        control_layout.addWidget(export_btn)
        
        # Auto-scroll checkbox
        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        control_layout.addWidget(self.auto_scroll_check)
        
        layout.addLayout(control_layout)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Courier", 9))
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #555;
            }
        """)
        layout.addWidget(self.log_display)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.log_count_label = QLabel("Logs: 0")
        status_layout.addWidget(self.log_count_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        self.setLayout(layout)
        self.logs = []
    
    def _setup_log_monitor(self):
        """Setup log monitoring"""
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self._poll_new_logs)
        self.log_timer.start(500)  # Poll every 500ms
        
        # Add sample logs
        self._add_sample_logs()
    
    def _add_sample_logs(self):
        """Add sample logs for demo"""
        sample_logs = [
            {"timestamp": datetime.now().isoformat(), "level": "INFO", "module": "Router", "message": "Engine routing started"},
            {"timestamp": datetime.now().isoformat(), "level": "DEBUG", "module": "RateLimiter", "message": "Rate limit check for example.com"},
            {"timestamp": datetime.now().isoformat(), "level": "INFO", "module": "FastEngine", "message": "Extraction successful: 3 media items"},
            {"timestamp": datetime.now().isoformat(), "level": "WARNING", "module": "ResourceGuard", "message": "Memory usage at 78%"},
            {"timestamp": datetime.now().isoformat(), "level": "INFO", "module": "DownloadManager", "message": "Download started: video.mp4"},
            {"timestamp": datetime.now().isoformat(), "level": "ERROR", "module": "StealthEngine", "message": "Access denied - HTTP 403"},
        ]
        
        for log in sample_logs:
            self.logs.append(log)
        
        self._refresh_display()
    
    def add_log(self, log_entry: dict):
        """Add a log entry"""
        self.logs.append(log_entry)
        if len(self.logs) > self.max_logs_spin.value():
            self.logs.pop(0)
        
        self._refresh_display()
    
    def _poll_new_logs(self):
        """Poll for new logs periodically"""
        self._refresh_display()
    
    def _refresh_display(self, logs=None):
        """Refresh the log display"""
        logs = logs if logs is not None else self.logs
        self.log_display.clear()
        cursor = self.log_display.textCursor()
        
        for log in logs[-self.max_logs_spin.value():]:
            self._append_log_entry(log)
        
        # Auto-scroll to bottom
        if self.auto_scroll_check.isChecked():
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.log_display.setTextCursor(cursor)
        
        self.log_count_label.setText(f"Logs: {len(logs)}")

    def _apply_filters(self):
        """Apply log filters"""
        search_text = self.search_box.text().lower()
        selected_level = self.level_filter.currentText()
        filtered_logs = []

        for log in self.logs:
            if selected_level != "All" and log.get("level", "").upper() != selected_level:
                continue
            if search_text:
                searchable = " ".join([str(log.get(key, "")).lower() for key in ["timestamp", "level", "module", "message"]])
                if search_text not in searchable:
                    continue
            filtered_logs.append(log)

        self._refresh_display(filtered_logs)
    
    def _append_log_entry(self, log: dict):
        """Append a log entry with color coding"""
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        level = log.get("level", "INFO")
        timestamp = log.get("timestamp", "").split("T")[-1][:8]
        module = log.get("module", "")
        message = log.get("message", "")
        
        # Create formatted text
        char_format = QTextCharFormat()
        
        # Color by level
        level_colors = {
            "DEBUG": QColor(128, 128, 128),
            "INFO": QColor(100, 200, 100),
            "WARNING": QColor(255, 193, 7),
            "ERROR": QColor(244, 67, 54),
            "CRITICAL": QColor(156, 39, 176)
        }
        char_format.setForeground(level_colors.get(level, QColor(200, 200, 200)))
        
        cursor.setCharFormat(char_format)
        cursor.insertText(f"[{timestamp}] ")
        
        char_format.setForeground(QColor(150, 150, 255))
        cursor.setCharFormat(char_format)
        cursor.insertText(f"{level:8} ")
        
        char_format.setForeground(QColor(200, 150, 100))
        cursor.setCharFormat(char_format)
        cursor.insertText(f"{module:15}")
        
        char_format.setForeground(QColor(200, 200, 200))
        cursor.setCharFormat(char_format)
        cursor.insertText(f" {message}\n")
        
        self.log_display.setTextCursor(cursor)
    
    def _clear_logs(self):
        """Clear all logs"""
        self.logs.clear()
        self.log_display.clear()
        self.log_count_label.setText("Logs: 0")
    
    def _export_logs(self):
        """Export logs to file"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Logs", "", "JSON Files (*.json);;Text Files (*.txt)"
        )
        
        if file_path:
            try:
                if file_path.endswith(".json"):
                    with open(file_path, "w") as f:
                        json.dump(self.logs, f, indent=2)
                else:
                    with open(file_path, "w") as f:
                        for log in self.logs:
                            f.write(f"{log}\n")
                
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Success", f"Logs exported to {file_path}")
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", f"Failed to export logs: {e}")
