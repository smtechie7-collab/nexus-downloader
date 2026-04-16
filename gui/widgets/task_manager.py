"""
Task Manager Widget - Monitor and control tasks
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QComboBox, QLabel, QHeaderView, QMessageBox,
    QDialog, QSpinBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QIcon
from datetime import datetime


class TaskManagerWidget(QWidget):
    """Widget for monitoring and managing download tasks"""
    
    task_action_requested = pyqtSignal(str, str)  # action, task_id
    
    def __init__(self):
        super().__init__()
        self._init_ui()
        self._setup_auto_refresh()
    
    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Control bar
        control_layout = QHBoxLayout()
        
        # Search
        control_layout.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter by URL or task ID...")
        self.search_box.textChanged.connect(self._filter_tasks)
        control_layout.addWidget(self.search_box)
        
        # Status filter
        control_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Pending", "Running", "Paused", "Completed", "Failed", "Cancelled"])
        self.status_filter.currentTextChanged.connect(self._filter_tasks)
        control_layout.addWidget(self.status_filter)
        
        # Action buttons
        self.pause_btn = QPushButton("⏸ Pause Selected")
        self.pause_btn.clicked.connect(self._pause_task)
        control_layout.addWidget(self.pause_btn)
        
        self.resume_btn = QPushButton("▶ Resume Selected")
        self.resume_btn.clicked.connect(self._resume_task)
        control_layout.addWidget(self.resume_btn)
        
        self.cancel_btn = QPushButton("✕ Cancel Selected")
        self.cancel_btn.setStyleSheet("background-color: #f44336; color: white;")
        self.cancel_btn.clicked.connect(self._cancel_task)
        control_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(control_layout)
        
        # Task table
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(8)
        self.task_table.setHorizontalHeaderLabels([
            "Task ID", "URL", "Status", "Progress", "Engine",
            "Created", "Error", "Actions"
        ])
        self.table = self.task_table
        
        # Set column widths
        header = self.task_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        
        self.task_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.task_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.task_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #555;
                background-color: #2b2b2b;
                alternate-background-color: #3b3b3b;
            }
            QTableWidget::item:selected {
                background-color: #0d47a1;
            }
        """)
        
        layout.addWidget(self.task_table)
        
        # Statistics bar
        stats_layout = QHBoxLayout()
        self.total_tasks_label = QLabel("Total: 0")
        self.running_tasks_label = QLabel("Running: 0")
        self.completed_tasks_label = QLabel("Completed: 0")
        self.failed_tasks_label = QLabel("Failed: 0")
        
        stats_layout.addWidget(self.total_tasks_label)
        stats_layout.addWidget(self.running_tasks_label)
        stats_layout.addWidget(self.completed_tasks_label)
        stats_layout.addWidget(self.failed_tasks_label)
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
        
        self.setLayout(layout)
        self.task_table.setRowCount(0)
        self._update_statistics()
    
    def _setup_auto_refresh(self):
        """Setup auto-refresh timer"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_tasks)
        self.refresh_timer.start(2000)  # Refresh every 2 seconds
    
    def _populate_sample_tasks(self):
        """Populate with sample tasks for demo"""
        sample_tasks = [
            {
                "id": "task_001",
                "url": "https://example.com/video1.mp4",
                "status": "Running",
                "progress": 45,
                "engine": "fast_engine_v1",
                "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "error": ""
            },
            {
                "id": "task_002",
                "url": "https://youtube.com/watch?v=abc123",
                "status": "Pending",
                "progress": 0,
                "engine": "media_engine_v1",
                "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "error": ""
            },
            {
                "id": "task_003",
                "url": "https://example.com/media",
                "status": "Completed",
                "progress": 100,
                "engine": "spider_engine_v1",
                "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "error": ""
            },
            {
                "id": "task_004",
                "url": "https://blocked.com/content",
                "status": "Failed",
                "progress": 0,
                "engine": "stealth_engine_v1",
                "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "error": "Access Denied (403)"
            },
        ]
        
        self._add_tasks_to_table(sample_tasks)
        self._update_statistics()
    
    def _add_tasks_to_table(self, tasks):
        """Add tasks to the table"""
        self.task_table.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            # Task ID
            id_item = QTableWidgetItem(task["id"])
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.task_table.setItem(row, 0, id_item)
            
            # URL
            url_item = QTableWidgetItem(task["url"])
            url_item.setToolTip(task["url"])
            self.task_table.setItem(row, 1, url_item)
            
            # Status
            status_item = QTableWidgetItem(task["status"])
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_colors = {
                "Running": QColor(76, 175, 80),
                "Pending": QColor(255, 193, 7),
                "Paused": QColor(158, 158, 158),
                "Completed": QColor(33, 150, 243),
                "Failed": QColor(244, 67, 54),
                "Cancelled": QColor(96, 125, 139)
            }
            status_item.setBackground(status_colors.get(task["status"], QColor(100, 100, 100)))
            self.task_table.setItem(row, 2, status_item)
            
            # Progress
            progress_item = QTableWidgetItem(f"{task['progress']}%")
            progress_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.task_table.setItem(row, 3, progress_item)
            
            # Engine
            engine_item = QTableWidgetItem(task["engine"])
            self.task_table.setItem(row, 4, engine_item)
            
            # Created
            created_item = QTableWidgetItem(task["created"])
            self.task_table.setItem(row, 5, created_item)
            
            # Error
            error_item = QTableWidgetItem(task["error"])
            error_item.setForeground(QColor(244, 67, 54))
            self.task_table.setItem(row, 6, error_item)
            
            # Actions
            action_item = QTableWidgetItem("View Details")
            action_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            action_item.setForeground(QColor(33, 150, 243))
            self.task_table.setItem(row, 7, action_item)
    
    def set_tasks(self, tasks):
        """Populate the task table with the provided task list."""
        self._add_tasks_to_table(tasks)
        self._update_statistics()

    def _pause_task(self):
        """Pause selected task"""
        current_row = self.task_table.currentRow()
        if current_row >= 0:
            task_id = self.task_table.item(current_row, 0).text()
            self.task_action_requested.emit("pause", task_id)
            QMessageBox.information(self, "Success", f"Task {task_id} paused")
    
    def _resume_task(self):
        """Resume selected task"""
        current_row = self.task_table.currentRow()
        if current_row >= 0:
            task_id = self.task_table.item(current_row, 0).text()
            self.task_action_requested.emit("resume", task_id)
            QMessageBox.information(self, "Success", f"Task {task_id} resumed")
    
    def _cancel_task(self):
        """Cancel selected task"""
        current_row = self.task_table.currentRow()
        if current_row >= 0:
            task_id = self.task_table.item(current_row, 0).text()
            reply = QMessageBox.question(self, "Confirm", f"Cancel task {task_id}?")
            if reply == QMessageBox.StandardButton.Yes:
                self.task_action_requested.emit("cancel", task_id)
                QMessageBox.information(self, "Success", f"Task {task_id} cancelled")
    
    def _filter_tasks(self):
        """Filter tasks based on search and status"""
        search_text = self.search_box.text().lower()
        status_filter = self.status_filter.currentText()
        
        for row in range(self.task_table.rowCount()):
            url = self.task_table.item(row, 1).text().lower()
            task_id = self.task_table.item(row, 0).text().lower()
            status = self.task_table.item(row, 2).text()
            
            # Check search
            matches_search = search_text in url or search_text in task_id
            
            # Check status
            matches_status = status_filter == "All" or status == status_filter
            
            # Show/hide row
            self.task_table.setRowHidden(row, not (matches_search and matches_status))
    
    def _refresh_tasks(self):
        """Refresh task list (would connect to backend in production)"""
        self._update_statistics()
    
    def _update_statistics(self):
        """Update statistics labels"""
        total = self.task_table.rowCount()
        running = sum(1 for row in range(total) if self.task_table.item(row, 2).text() == "Running")
        completed = sum(1 for row in range(total) if self.task_table.item(row, 2).text() == "Completed")
        failed = sum(1 for row in range(total) if self.task_table.item(row, 2).text() == "Failed")
        
        self.total_tasks_label.setText(f"Total: {total}")
        self.running_tasks_label.setText(f"Running: {running}")
        self.completed_tasks_label.setText(f"Completed: {completed}")
        self.failed_tasks_label.setText(f"Failed: {failed}")
