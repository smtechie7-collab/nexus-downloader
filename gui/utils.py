"""
GUI Utilities and Helper Functions
"""

from PyQt6.QtWidgets import (
    QMessageBox, QFileDialog, QDialog, QVBoxLayout, 
    QLabel, QProgressBar, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QColor, QFont
from typing import Optional, Callable, Any
import json


class MessageBox:
    """Utility class for showing message boxes"""
    
    @staticmethod
    def info(parent: Optional[QWidget], title: str, message: str):
        """Show info message box"""
        QMessageBox.information(parent, title, message)
    
    @staticmethod
    def warning(parent: Optional[QWidget], title: str, message: str):
        """Show warning message box"""
        QMessageBox.warning(parent, title, message)
    
    @staticmethod
    def error(parent: Optional[QWidget], title: str, message: str):
        """Show error message box"""
        QMessageBox.critical(parent, title, message)
    
    @staticmethod
    def question(parent: Optional[QWidget], title: str, message: str) -> bool:
        """Show yes/no question dialog"""
        reply = QMessageBox.question(parent, title, message,
                                     QMessageBox.StandardButton.Yes | 
                                     QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes


class FileDialog:
    """Utility class for file dialogs"""
    
    @staticmethod
    def get_open_file(parent: Optional[QWidget], 
                     title: str = "Open File",
                     filter_: str = "All Files (*)") -> Optional[str]:
        """Get file path for opening"""
        path, _ = QFileDialog.getOpenFileName(parent, title, "", filter_)
        return path if path else None
    
    @staticmethod
    def get_save_file(parent: Optional[QWidget],
                     title: str = "Save File",
                     filter_: str = "All Files (*)") -> Optional[str]:
        """Get file path for saving"""
        path, _ = QFileDialog.getSaveFileName(parent, title, "", filter_)
        return path if path else None
    
    @staticmethod
    def get_directory(parent: Optional[QWidget],
                     title: str = "Select Directory") -> Optional[str]:
        """Get directory path"""
        path = QFileDialog.getExistingDirectory(parent, title)
        return path if path else None


class ProgressDialog(QDialog):
    """Custom progress dialog"""
    
    def __init__(self, parent: Optional[QWidget] = None, 
                 title: str = "Processing", 
                 maximum: int = 100):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumWidth(350)
        self.setMinimumHeight(100)
        
        layout = QVBoxLayout()
        
        self.label = QLabel("Processing...")
        layout.addWidget(self.label)
        
        self.progress = QProgressBar()
        self.progress.setMaximum(maximum)
        layout.addWidget(self.progress)
        
        self.setLayout(layout)
    
    def set_label(self, text: str):
        """Update label text"""
        self.label.setText(text)
    
    def set_value(self, value: int):
        """Update progress value"""
        self.progress.setValue(value)
    
    def set_maximum(self, maximum: int):
        """Set maximum value"""
        self.progress.setMaximum(maximum)


class BackgroundWorker(QThread):
    """Base class for running long operations in background thread"""
    
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(dict)
    
    def __init__(self, task: Callable, *args, **kwargs):
        super().__init__()
        self.task = task
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        """Run the task in background"""
        try:
            result = self.task(*self.args, **self.kwargs)
            self.result.emit(result if isinstance(result, dict) else {"data": result})
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f}{unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f}PB"


def format_duration(seconds: float) -> str:
    """Format duration to human readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def get_status_color(status: str) -> QColor:
    """Get color for task status"""
    colors = {
        "pending": QColor("#FFB300"),      # Orange
        "running": QColor("#4CAF50"),      # Green
        "paused": QColor("#2196F3"),       # Blue
        "completed": QColor("#8BC34A"),    # Light Green
        "failed": QColor("#F44336"),       # Red
        "cancelled": QColor("#9E9E9E"),    # Gray
    }
    return colors.get(status.lower(), QColor("#2196F3"))


def get_level_color(level: str) -> QColor:
    """Get color for log level"""
    colors = {
        "DEBUG": QColor("#A0A0A0"),     # Gray
        "INFO": QColor("#4CAF50"),      # Green
        "WARNING": QColor("#FFC107"),   # Amber
        "ERROR": QColor("#F44336"),     # Red
        "CRITICAL": QColor("#9C27B0"),  # Purple
    }
    return colors.get(level.upper(), QColor("#4CAF50"))


def load_config_file(path: str) -> dict:
    """Load JSON configuration file"""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {}


def save_config_file(path: str, data: dict):
    """Save JSON configuration file"""
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        return False


class DataTable:
    """Helper for table operations"""
    
    @staticmethod
    def get_row_data(table, row: int) -> dict:
        """Extract row data from table"""
        data = {}
        for col in range(table.columnCount()):
            item = table.item(row, col)
            if item:
                data[table.horizontalHeaderItem(col).text()] = item.text()
        return data
    
    @staticmethod
    def get_selected_rows(table) -> list:
        """Get all selected row indices"""
        return [idx.row() for idx in table.selectedIndexes()]
    
    @staticmethod
    def add_row(table, data: list):
        """Add row to table"""
        row_pos = table.rowCount()
        table.insertRow(row_pos)
        for col, value in enumerate(data):
            table.setItem(row_pos, col, value)
