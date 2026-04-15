"""
Dashboard Widget - Real-time system overview and key metrics
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QProgressBar,
    QGridLayout, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor


class DashboardWidget(QWidget):
    """Dashboard with real-time metrics overview"""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        """Initialize dashboard UI"""
        layout = QVBoxLayout()
        
        # Top metrics row
        metrics_layout = QHBoxLayout()
        
        # Total requests
        self.total_requests_widget = self._create_metric_card("Total Requests", "0", "#2196F3")
        metrics_layout.addWidget(self.total_requests_widget)
        
        # Success rate
        self.success_rate_widget = self._create_metric_card("Success Rate", "0%", "#4CAF50")
        metrics_layout.addWidget(self.success_rate_widget)
        
        # Failed requests
        self.failed_requests_widget = self._create_metric_card("Failed", "0", "#F44336")
        metrics_layout.addWidget(self.failed_requests_widget)
        
        # Downloaded bytes
        self.bytes_downloaded_widget = self._create_metric_card("Downloaded", "0 MB", "#FF9800")
        metrics_layout.addWidget(self.bytes_downloaded_widget)
        
        layout.addLayout(metrics_layout)
        
        # Charts section
        charts_layout = QHBoxLayout()
        
        # Success/Failure pie chart
        self.pie_chart = self._create_pie_chart()
        charts_layout.addWidget(self.pie_chart)
        
        # Status indicators
        status_layout = QVBoxLayout()
        status_layout.addWidget(QLabel("System Status"))
        
        self.status_labels = {}
        for status_name in ["Requests/sec", "Avg Latency", "Memory Usage", "CPU Usage"]:
            status_widget = self._create_status_indicator(status_name, "0")
            self.status_labels[status_name] = status_widget
            status_layout.addWidget(status_widget)
        
        charts_layout.addLayout(status_layout)
        
        layout.addLayout(charts_layout)
        self.setLayout(layout)
    
    def _create_metric_card(self, title: str, value: str, color: str) -> QGroupBox:
        """Create a metric card widget"""
        card = QGroupBox(title)
        card_layout = QVBoxLayout()
        
        value_label = QLabel(value)
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        value_label.setFont(font)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card_layout.addWidget(value_label)
        card.setLayout(card_layout)
        
        # Set color border
        card.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid {color};
                border-radius: 5px;
                padding: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }}
        """)
        
        # Store value label for updates
        card.value_label = value_label
        
        return card
    
    def _create_pie_chart(self) -> QWidget:
        """Create simple success/failure display"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("Request Success Distribution")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Success progress bar
        self.success_label = QLabel("Success: 75%")
        self.success_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        layout.addWidget(self.success_label)
        
        self.success_bar = QProgressBar()
        self.success_bar.setValue(75)
        self.success_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        layout.addWidget(self.success_bar)
        
        # Failed progress bar
        self.failed_label = QLabel("Failed: 25%")
        self.failed_label.setStyleSheet("color: #F44336; font-weight: bold;")
        layout.addWidget(self.failed_label)
        
        self.failed_bar = QProgressBar()
        self.failed_bar.setValue(25)
        self.failed_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #F44336;
            }
        """)
        layout.addWidget(self.failed_bar)
        
        widget.setLayout(layout)
        return widget
    
    def _create_status_indicator(self, name: str, value: str) -> QFrame:
        """Create a status indicator box"""
        frame = QFrame()
        layout = QHBoxLayout()
        
        name_label = QLabel(name)
        name_label.setMinimumWidth(100)
        
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        value_label.setMinimumWidth(100)
        font = QFont()
        font.setBold(True)
        value_label.setFont(font)
        
        layout.addWidget(name_label)
        layout.addStretch()
        layout.addWidget(value_label)
        
        frame.setLayout(layout)
        frame.setStyleSheet("""
            QFrame {
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
                background-color: #2b2b2b;
            }
        """)
        
        frame.value_label = value_label
        return frame
    
    def update_metrics(self, summary: dict):
        """Update dashboard with new metrics"""
        try:
            total = summary.get('total_requests', 0)
            successes = summary.get('total_successes', 0)
            failures = summary.get('total_failures', 0)
            bytes_dl = summary.get('total_bytes_downloaded', 0)
            
            success_rate = (successes / total * 100) if total > 0 else 0
            
            # Update metric cards
            self.total_requests_widget.value_label.setText(str(total))
            self.success_rate_widget.value_label.setText(f"{success_rate:.1f}%")
            self.failed_requests_widget.value_label.setText(str(failures))
            
            bytes_mb = bytes_dl / (1024 ** 2)
            self.bytes_downloaded_widget.value_label.setText(f"{bytes_mb:.2f} MB")
            
            # Update progress bars (simplified chart replacement)
            if hasattr(self, 'success_bar') and hasattr(self, 'failed_bar'):
                self.success_bar.setValue(int(success_rate))
                self.failed_bar.setValue(int((failures / total * 100) if total > 0 else 0))
                
                # Update labels
                if hasattr(self, 'success_label') and hasattr(self, 'failed_label'):
                    self.success_label.setText(f"Success: {success_rate:.1f}%")
                    failed_rate = (failures / total * 100) if total > 0 else 0
                    self.failed_label.setText(f"Failed: {failed_rate:.1f}%")
        
        except Exception as e:
            print(f"Dashboard update error: {e}")
