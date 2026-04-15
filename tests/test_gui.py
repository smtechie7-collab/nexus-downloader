"""
GUI Integration Tests
Test the PyQt6 desktop application components
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Skip GUI tests if PyQt6 not available
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False

if PYQT6_AVAILABLE:
    from gui.app import NexusDownloaderApp
    from gui.widgets.dashboard import DashboardWidget
    from gui.widgets.task_manager import TaskManagerWidget
    from gui.widgets.metrics_viewer import MetricsViewerWidget
    from gui.widgets.log_viewer import LogViewerWidget
    from gui.widgets.settings_panel import SettingsPanelWidget


@pytest.mark.skipif(not PYQT6_AVAILABLE, reason="PyQt6 not available")
class TestGUIComponents:
    """Test GUI components"""

    @pytest.fixture(scope="class")
    def app(self):
        """Create QApplication instance"""
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        yield app

    def test_main_window_creation(self, app):
        """Test main window can be created"""
        window = NexusDownloaderApp()
        assert window.windowTitle() == "Nexus Downloader - Media Extraction Platform"
        assert window.geometry().width() == 1400
        assert window.geometry().height() == 900

    def test_dashboard_widget(self, app):
        """Test dashboard widget creation"""
        widget = DashboardWidget()
        assert widget is not None
        # Check if metric cards are created
        assert hasattr(widget, 'metric_cards')
        assert len(widget.metric_cards) == 4

    def test_task_manager_widget(self, app):
        """Test task manager widget creation"""
        widget = TaskManagerWidget()
        assert widget is not None
        assert hasattr(widget, 'table')
        assert widget.table.columnCount() == 8

    def test_metrics_viewer_widget(self, app):
        """Test metrics viewer widget creation"""
        widget = MetricsViewerWidget()
        assert widget is not None
        assert hasattr(widget, 'tabs')
        assert widget.tabs.count() == 3

    def test_log_viewer_widget(self, app):
        """Test log viewer widget creation"""
        widget = LogViewerWidget()
        assert widget is not None
        assert hasattr(widget, 'log_display')
        assert hasattr(widget, 'level_filter')

    def test_settings_panel_widget(self, app):
        """Test settings panel widget creation"""
        widget = SettingsPanelWidget()
        assert widget is not None
        assert hasattr(widget, 'tabs')
        assert widget.tabs.count() == 5

    @patch('monitoring.metrics.get_metrics')
    def test_metrics_integration(self, mock_get_metrics, app):
        """Test metrics integration"""
        mock_get_metrics.return_value = {
            'summary': {
                'total_requests': 100,
                'success_rate': 85.5,
                'failed_count': 15,
                'downloaded_bytes': 1024000
            },
            'domain_stats': {},
            'engine_stats': {},
            'error_stats': {}
        }

        widget = DashboardWidget()
        widget.update_metrics()

        # Check if metrics were updated
        assert widget.metric_cards[0].value_label.text() == "100"
        assert widget.metric_cards[1].value_label.text() == "85.5%"
        assert widget.metric_cards[2].value_label.text() == "15"
        assert widget.metric_cards[3].value_label.text() == "1000.0 KB"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
