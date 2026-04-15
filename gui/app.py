"""
Nexus Downloader - Production-Grade PyQt6 Desktop Application
Modern UI with real-time metrics, task management, and system monitoring
"""

import sys
import asyncio
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QTabWidget, QStatusBar, QLabel, QProgressBar, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QIcon, QColor, QFont
import pyqtdarktheme

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from gui.widgets.dashboard import DashboardWidget
from gui.widgets.task_manager import TaskManagerWidget
from gui.widgets.metrics_viewer import MetricsViewerWidget
from gui.widgets.log_viewer import LogViewerWidget
from gui.widgets.settings_panel import SettingsPanelWidget
from gui.styles import apply_stylesheet
from monitoring.metrics import get_metrics
from monitoring.logger import get_logger

logger = get_logger("UIApplication")


class MetricsUpdater(QObject):
    """Worker thread for updating metrics in real-time"""
    metrics_updated = pyqtSignal(dict)
    
    def __init__(self, interval_ms: int = 1000):
        super().__init__()
        self.interval_ms = interval_ms
        self.running = True
    
    def update_metrics(self):
        """Fetch and emit metrics updates"""
        while self.running:
            try:
                metrics = get_metrics()
                data = {
                    'summary': metrics.get_summary(),
                    'domain_stats': metrics.get_domain_stats(),
                    'engine_stats': metrics.get_engine_stats(),
                }
                self.metrics_updated.emit(data)
            except Exception as e:
                logger.error("Metrics update failed", extra={"context": {"error": str(e)}})
            
            asyncio.sleep(self.interval_ms / 1000.0)
    
    def stop(self):
        """Stop the updater"""
        self.running = False


class NexusDownloaderApp(QMainWindow):
    """
    Main Application Window
    Production-grade PyQt6 desktop application for Nexus Downloader
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nexus Downloader - Media Extraction Platform")
        self.setWindowIcon(self._create_icon())
        self.setGeometry(100, 100, 1400, 900)
        
        # Apply dark theme
        self.setStyle(pyqtdarktheme.setup_theme())
        
        # Initialize UI
        self._init_ui()
        self._setup_metrics_updater()
        
        logger.info("Application initialized")
    
    def _create_icon(self) -> QIcon:
        """Create application icon"""
        from PyQt6.QtGui import QPixmap
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 120, 215))
        return QIcon(pixmap)
    
    def _init_ui(self):
        """Initialize the user interface"""
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Create dashboard widget
        self.dashboard = DashboardWidget()
        tabs.addTab(self.dashboard, "📊 Dashboard")
        
        # Create task manager widget
        self.task_manager = TaskManagerWidget()
        tabs.addTab(self.task_manager, "📋 Tasks")
        
        # Create metrics viewer widget
        self.metrics_viewer = MetricsViewerWidget()
        tabs.addTab(self.metrics_viewer, "📈 Metrics")
        
        # Create log viewer widget
        self.log_viewer = LogViewerWidget()
        tabs.addTab(self.log_viewer, "📝 Logs")
        
        # Create settings panel
        self.settings_panel = SettingsPanelWidget()
        tabs.addTab(self.settings_panel, "⚙️ Settings")
        
        main_layout.addWidget(tabs)
        
        # Status bar
        self._setup_status_bar()
        
        # Connect signals
        self._connect_signals()
    
    def _setup_status_bar(self):
        """Setup status bar with real-time info"""
        self.status_label = QLabel("Ready")
        self.request_counter = QLabel("Requests: 0")
        self.success_rate_label = QLabel("Success: 0%")
        self.memory_label = QLabel("Memory: 0 MB")
        
        self.statusBar().addWidget(self.status_label, 1)
        self.statusBar().addWidget(self.request_counter)
        self.statusBar().addWidget(self.success_rate_label)
        self.statusBar().addWidget(self.memory_label)
    
    def _setup_metrics_updater(self):
        """Setup timer for periodic metrics updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_metrics)
        self.update_timer.start(1000)  # Update every second
    
    def _update_metrics(self):
        """Update displayed metrics"""
        try:
            metrics = get_metrics()
            summary = metrics.get_summary()
            
            # Update status bar
            total = summary.get('total_requests', 0)
            success = summary.get('total_successes', 0)
            success_rate = (success / total * 100) if total > 0 else 0
            
            self.request_counter.setText(f"Requests: {total}")
            self.success_rate_label.setText(f"Success: {success_rate:.1f}%")
            
            # Update memory usage
            import psutil
            memory_mb = psutil.Process().memory_info().rss / (1024 ** 2)
            self.memory_label.setText(f"Memory: {memory_mb:.1f} MB")
            
            # Update widgets
            self.dashboard.update_metrics(summary)
            self.metrics_viewer.update_metrics(summary, metrics.get_domain_stats(), metrics.get_engine_stats())
            
        except Exception as e:
            logger.error("Metrics display failed", extra={"context": {"error": str(e)}})
    
    def _connect_signals(self):
        """Connect signals between components"""
        self.task_manager.task_action_requested.connect(self._handle_task_action)
    
    def _handle_task_action(self, action: str, task_id: str):
        """Handle task manager actions"""
        logger.info("Task action requested", extra={
            "context": {"action": action, "task_id": task_id}
        })
    
    def closeEvent(self, event):
        """Handle application close"""
        self.update_timer.stop()
        logger.info("Application closed")
        event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Apply theme
    app.setStyle(pyqtdarktheme.setup_theme("auto"))
    
    # Create and show main window
    window = NexusDownloaderApp()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
