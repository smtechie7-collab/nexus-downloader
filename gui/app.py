"""
Nexus Downloader - Production-Grade PyQt6 Desktop Application
Dual-Mode UI: Simple Mode (Beginners) + Advanced Mode (Power Users)
"""

import os
import sys
import asyncio
import time
import urllib.parse
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QTabWidget, QStatusBar, QLabel, QProgressBar, QPushButton, QLineEdit,
    QSplitter, QGroupBox, QFormLayout, QComboBox, QSpinBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QTextEdit, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread, QSettings
from PyQt6.QtGui import QIcon, QColor, QFont
from datetime import datetime
import uuid

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from gui.widgets.dashboard import DashboardWidget
from gui.widgets.task_manager import TaskManagerWidget
from gui.widgets.metrics_viewer import MetricsViewerWidget
from gui.widgets.log_viewer import LogViewerWidget
from gui.widgets.settings_panel import SettingsPanelWidget
from gui.styles import apply_stylesheet, COLORS
from core.router import Router
from core.priority_queue import TaskQueue
from core.resource_guard import ResourceGuard
from downloader.download_manager import DownloadManager
from engines.fast_engine_v1 import FastEngineV1
from engines.headless_engine_v1 import HeadlessEngineV1
from engines.media_engine_v1 import MediaEngineV1
from engines.spider_engine_v1 import SpiderEngineV1
from engines.stealth_engine_v1 import StealthEngineV1
from storage.deduplicator import Deduplicator
from storage.cache import CacheLayer
from pipeline.validator import validate_media
from pipeline.parser import URLParser
from network.ssrf_guard import SSRFGuard
from utils.constants import Priority
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
            
            time.sleep(self.interval_ms / 1000.0)


class NexusDownloaderApp(QMainWindow):
    """
    Main Application Window with Dual-Mode Support
    Simple Mode: For beginners - Clean, minimal interface
    Advanced Mode: For power users - Full features & controls
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nexus Downloader - Media Extraction Platform")
        self.setWindowIcon(self._create_icon())
        self.setGeometry(100, 100, 1400, 900)
        
        # Settings for mode persistence
        self.settings = QSettings("NexusDownloader", "NexusDownloader")
        self.advanced_mode = self.settings.value("advanced_mode", False, type=bool)
        
        # Initialize UI and pipeline
        self._init_ui()
        self._init_pipeline()
        self._setup_metrics_updater()
        
        logger.info("Application initialized", extra={"context": {"mode": "advanced" if self.advanced_mode else "simple"}})
    
    def _create_icon(self) -> QIcon:
        """Create application icon"""
        from PyQt6.QtGui import QPixmap
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 120, 215))
        return QIcon(pixmap)
    
    def _init_ui(self):
        """Initialize the user interface with header and mode toggle"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Header with mode toggle
        self._create_header(main_layout)
        
        # Content area (will change based on mode)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        main_layout.addWidget(self.content_widget)
        
        # Load current mode
        self._load_mode()
        
        # Status bar
        self._setup_status_bar()
        
        # Connect signals
        self._connect_signals()
    
    def _create_header(self, parent_layout):
        """Create header with mode toggle and title"""
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("Nexus Downloader")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Mode selector
        mode_label = QLabel("Mode:")
        header_layout.addWidget(mode_label)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Simple (Beginner)", "Advanced (Power User)"])
        self.mode_combo.setCurrentIndex(1 if self.advanced_mode else 0)
        self.mode_combo.currentIndexChanged.connect(self._switch_mode)
        self.mode_combo.setMaximumWidth(200)
        header_layout.addWidget(self.mode_combo)
        
        parent_layout.addLayout(header_layout)
    
    def _load_mode(self):
        """Load the appropriate UI based on current mode"""
        # Clear previous layout
        while self.content_layout.count():
            self.content_layout.takeAt(0).widget().deleteLater()
        
        if self.advanced_mode:
            self._create_advanced_mode()
        else:
            self._create_simple_mode()

        self._connect_signals()
    
    def _create_simple_mode(self):
        """Simple mode interface for beginners"""
        # Main download form
        form_group = QGroupBox("Download Media")
        form_layout = QFormLayout()
        
        # URL input
        url_label = QLabel("Media URL:")
        url_label.setToolTip("Paste the video/media URL here")
        self.simple_url_input = QLineEdit()
        self.simple_url_input.setPlaceholderText("https://example.com/video.mp4")
        form_layout.addRow(url_label, self.simple_url_input)
        
        # Output folder
        output_label = QLabel("Save to:")
        output_label.setToolTip("Where to save downloaded files")
        self.simple_output_input = QLineEdit()
        self.simple_output_input.setText(str(Path.home() / "Downloads"))
        self.simple_output_input.setPlaceholderText(str(Path.home() / "Downloads"))
        form_layout.addRow(output_label, self.simple_output_input)
        
        # Quality selector
        quality_label = QLabel("Quality:")
        quality_label.setToolTip("Choose download quality (if available)")
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Auto", "480p", "720p", "1080p", "4K"])
        form_layout.addRow(quality_label, self.quality_combo)
        
        form_group.setLayout(form_layout)
        self.content_layout.addWidget(form_group)
        
        # Progress section
        progress_group = QGroupBox("Download Progress")
        progress_layout = QVBoxLayout()
        
        # File name display
        self.simple_filename_label = QLabel("No file selected")
        self.simple_filename_label.setStyleSheet("color: #888;")
        progress_layout.addWidget(self.simple_filename_label)
        
        # Progress bar
        self.simple_progress = QProgressBar()
        self.simple_progress.setMinimum(0)
        self.simple_progress.setMaximum(100)
        self.simple_progress.setValue(0)
        progress_layout.addWidget(self.simple_progress)
        
        # Speed and time display
        self.simple_speed_label = QLabel("Speed: 0 MB/s  |  Time Remaining: --")
        self.simple_speed_label.setStyleSheet("color: #0d7377;")
        progress_layout.addWidget(self.simple_speed_label)
        
        progress_group.setLayout(progress_layout)
        self.content_layout.addWidget(progress_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.simple_start_btn = QPushButton("Start Download")
        self.simple_start_btn.setMinimumHeight(40)
        self.simple_start_btn.setStyleSheet("background-color: #0d7377; color: white; font-weight: bold;")
        self.simple_start_btn.clicked.connect(self._on_simple_start)
        button_layout.addWidget(self.simple_start_btn)
        
        self.simple_pause_btn = QPushButton("Pause")
        self.simple_pause_btn.setMinimumHeight(40)
        self.simple_pause_btn.clicked.connect(self._on_simple_pause)
        self.simple_pause_btn.setEnabled(False)
        button_layout.addWidget(self.simple_pause_btn)
        
        self.simple_cancel_btn = QPushButton("Cancel")
        self.simple_cancel_btn.setMinimumHeight(40)
        self.simple_cancel_btn.setStyleSheet("background-color: #ca3e1f;")
        self.simple_cancel_btn.clicked.connect(self._on_simple_cancel)
        self.simple_cancel_btn.setEnabled(False)
        button_layout.addWidget(self.simple_cancel_btn)
        
        self.content_layout.addLayout(button_layout)
        
        # Recent downloads
        recent_group = QGroupBox("Recent Downloads")
        recent_layout = QVBoxLayout()
        self.simple_recent = QTextEdit()
        self.simple_recent.setReadOnly(True)
        self.simple_recent.setMaximumHeight(150)
        self.simple_recent.setPlaceholderText("No downloads yet")
        recent_layout.addWidget(self.simple_recent)
        recent_group.setLayout(recent_layout)
        self.content_layout.addWidget(recent_group)
        
        self.content_layout.addStretch()
    
    def _create_advanced_mode(self):
        """Advanced mode with all features"""
        tabs = QTabWidget()
        
        # Create all advanced widgets
        self.dashboard = DashboardWidget()
        tabs.addTab(self.dashboard, "Dashboard")
        
        self.task_manager = TaskManagerWidget()
        tabs.addTab(self.task_manager, "Tasks")
        
        self.metrics_viewer = MetricsViewerWidget()
        tabs.addTab(self.metrics_viewer, "Metrics")
        
        self.log_viewer = LogViewerWidget()
        tabs.addTab(self.log_viewer, "Logs")
        
        self.settings_panel = SettingsPanelWidget()
        tabs.addTab(self.settings_panel, "Settings")
        
        self.content_layout.addWidget(tabs)
    
    def _switch_mode(self, index):
        """Switch between simple and advanced modes"""
        self.advanced_mode = (index == 1)
        self.settings.setValue("advanced_mode", self.advanced_mode)
        self._load_mode()
        logger.info("Mode switched", extra={"context": {"new_mode": "advanced" if self.advanced_mode else "simple"}})
    
    def _on_simple_start(self):
        """Start download in simple mode"""
        url = self.simple_url_input.text().strip()
        output_path = self.simple_output_input.text().strip()
        
        if not url:
            self.simple_filename_label.setText("ERROR: Please enter a URL")
            self.simple_filename_label.setStyleSheet("color: #ca3e1f;")
            return
        
        if not output_path:
            output_path = str(Path.home() / "Downloads")
            self.simple_output_input.setText(output_path)

        os.makedirs(output_path, exist_ok=True)
        self.simple_current_request_url = url
        self.simple_filename_label.setText(f"Downloading: {url}")
        self.simple_filename_label.setStyleSheet("color: #0d7377;")
        self.simple_progress.setValue(0)
        self.simple_speed_label.setText("Speed: 0 MB/s  |  Time Remaining: --")
        self.simple_start_btn.setEnabled(False)
        self.simple_pause_btn.setEnabled(True)
        self.simple_cancel_btn.setEnabled(True)
        self.simple_paused = False
        self._schedule_simple_download(url, output_path)
        logger.info("Simple download started", extra={"context": {"url": url, "output": output_path}})
    
    def _on_simple_pause(self):
        """Pause download in simple mode"""
        self.simple_paused = True
        self.simple_start_btn.setEnabled(True)
        self.simple_pause_btn.setEnabled(False)
        self.simple_filename_label.setText("Download paused")
        logger.info("Download paused")
    
    def _on_simple_cancel(self):
        """Cancel download in simple mode"""
        self.simple_paused = True
        self.simple_start_btn.setEnabled(True)
        self.simple_pause_btn.setEnabled(False)
        self.simple_cancel_btn.setEnabled(False)
        self.simple_progress.setValue(0)
        self.simple_filename_label.setText("Download cancelled")
        self.simple_filename_label.setStyleSheet("color: #888;")
        if self.simple_current_request_url:
            for task_id, task in self.pipeline_tasks.items():
                if task.get('request_url') == self.simple_current_request_url and task['status'] in ['Pending', 'Running']:
                    task['status'] = 'Cancelled'
            self._refresh_task_manager()
        logger.info("Download cancelled")
    
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

    def _init_pipeline(self):
        """Initialize backend pipeline objects and worker threads."""
        self.pipeline_tasks = {}
        self.simple_current_request_url = None
        self.simple_start_time = None
        self.simple_paused = False

        self.guard = ResourceGuard()
        self.router = Router()
        self.queue = TaskQueue()
        self.dedup = Deduplicator()
        self.cache = CacheLayer()
        self.download_manager = DownloadManager()
        self.ssrf_guard = SSRFGuard()
        self.url_parser = URLParser()

        self._register_engines()

        self.pipeline_loop = asyncio.new_event_loop()
        self.pipeline_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.pipeline_thread.start()

        self.download_thread = threading.Thread(target=self._download_worker, daemon=True)
        self.download_thread.start()

    def _register_engines(self):
        self.router.register_engine("fast_engine", FastEngineV1())
        self.router.register_engine("headless_engine", HeadlessEngineV1())
        self.router.register_engine("media_engine", MediaEngineV1())
        self.router.register_engine("spider_engine", SpiderEngineV1())
        self.router.register_engine("stealth_engine", StealthEngineV1())

    def _run_async_loop(self):
        asyncio.set_event_loop(self.pipeline_loop)
        self.pipeline_loop.run_forever()

    def _schedule_simple_download(self, url: str, output_path: str):
        self.simple_current_request_url = url
        self.simple_start_time = time.time()
        self.simple_paused = False
        future = asyncio.run_coroutine_threadsafe(
            self._process_url_request(url, output_path),
            self.pipeline_loop
        )
        future.add_done_callback(lambda f: self._on_request_processed(f, url))

    def _on_request_processed(self, future, url: str):
        try:
            future.result()
        except Exception as e:
            self._defer_ui_update(lambda: self._log_event("ERROR", f"Pipeline error for {url}: {e}", "Pipeline"))

    async def _process_url_request(self, url: str, output_path: str):
        if not self.ssrf_guard.validate_request(url):
            self._log_event("WARNING", f"URL blocked by SSRF protection: {url}", "SSRFGuard")
            return False

        parsed_info = self.url_parser.extract_media_info(url)
        normalized_url = parsed_info['normalized_url']
        self._log_event("INFO", f"URL normalized for download: {normalized_url}", "URLParser")

        if self.dedup.is_duplicate(normalized_url):
            self._log_event("WARNING", f"Duplicate media URL skipped: {normalized_url}", "Deduplicator")
            return False

        result = await self.router.route(normalized_url)
        if result.get('status') != 'success':
            self._log_event("ERROR", f"Extraction failed: {result.get('error_msg', 'unknown')}", "Router")
            return False

        media_list = result.get('media', [])
        if not media_list:
            self._log_event("WARNING", f"No media items discovered for URL: {url}", "Router")
            return False

        for media in media_list:
            valid = await validate_media(media)
            if not valid:
                self._log_event("WARNING", f"Media validation failed: {media.get('url')}", "Validator")
                continue

            task_id = uuid.uuid4().hex
            engine_name = result.get('source', 'unknown')
            title = media.get('metadata', {}).get('title') or parsed_info.get('title', 'download')
            filename = self._derive_filename(media.get('url', url), title)
            request_url = url

            self.pipeline_tasks[task_id] = {
                'id': task_id,
                'url': media.get('url', url),
                'status': 'Pending',
                'progress': 0,
                'engine': engine_name,
                'created': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'error': '',
                'request_url': request_url,
                'filename': filename,
                'output_path': output_path,
            }
            self.queue.add({
                'task_id': task_id,
                'url': media.get('url', url),
                'filename': filename,
                'output_path': output_path,
                'request_url': request_url,
                'engine': engine_name,
            }, Priority.HIGH)
            self._refresh_task_manager()
            self._log_event("INFO", f"Queued download task {task_id} for {filename}", "Pipeline")

        return True

    def _derive_filename(self, media_url: str, title: str) -> str:
        parsed = urllib.parse.urlparse(media_url)
        extension = os.path.splitext(parsed.path)[1] or '.bin'
        cleaned_title = title.strip().replace(' ', '_')
        return f"{cleaned_title}{extension}"

    def _download_worker(self):
        while True:
            task = self.queue.get(timeout=2)
            if task is None:
                continue

            task_id = task.get('task_id')
            if not task_id or task_id not in self.pipeline_tasks:
                continue

            if self.pipeline_tasks[task_id]['status'] in ['Cancelled', 'Paused']:
                self._log_event("INFO", f"Skipping task {task_id} because status is {self.pipeline_tasks[task_id]['status']}", "DownloadWorker")
                continue

            self.pipeline_tasks[task_id]['status'] = 'Running'
            self._defer_refresh()

            future = self.download_manager.download(
                task['url'],
                task['filename'],
                output_path=task.get('output_path'),
                task_id=task_id,
                progress_callback=lambda downloaded, total: self._download_progress_callback(task_id, downloaded, total)
            )

            success = False
            try:
                success = future.result()
            except Exception as e:
                self._log_event("ERROR", f"Download failed for task {task_id}: {e}", "DownloadWorker")

            if success and self.pipeline_tasks[task_id]['status'] != 'Cancelled':
                self.pipeline_tasks[task_id]['status'] = 'Completed'
                self.pipeline_tasks[task_id]['progress'] = 100
                self._log_event("INFO", f"Task {task_id} completed", "DownloadWorker")
                self._defer_ui_update(lambda: self._append_recent_download(self.pipeline_tasks[task_id]))
            elif not success and self.pipeline_tasks[task_id]['status'] != 'Cancelled':
                self.pipeline_tasks[task_id]['status'] = 'Failed'
                self.pipeline_tasks[task_id]['error'] = 'Download error'

            self._defer_refresh()

    def _download_progress_callback(self, task_id: str, downloaded: int, total: int):
        task = self.pipeline_tasks.get(task_id)
        if not task:
            return

        if total:
            task['progress'] = min(100, int(downloaded * 100 / total))
        else:
            task['progress'] = min(99, int(downloaded / 1024))

        if self.simple_current_request_url and task.get('request_url') == self.simple_current_request_url:
            self._defer_ui_update(lambda: self._update_simple_progress(task['progress'], downloaded, total))

        self._defer_refresh()

    def _update_simple_progress(self, progress: int, downloaded: int, total: int):
        self.simple_progress.setValue(progress)
        simple_label = f"Downloaded {downloaded // 1024} KB"
        if total:
            simple_label += f" / {total // 1024} KB"
        self.simple_speed_label.setText(f"Speed: -- | {simple_label}")

    def _append_recent_download(self, task: dict):
        if hasattr(self, 'simple_recent'):
            self.simple_recent.append(f"{task['filename']} ({task['url']}) - {task['status']}")

    def _defer_refresh(self):
        QTimer.singleShot(0, self._refresh_task_manager)

    def _defer_ui_update(self, callback):
        QTimer.singleShot(0, callback)

    def _refresh_task_manager(self):
        if self.advanced_mode and hasattr(self, 'task_manager'):
            self.task_manager.set_tasks(list(self.pipeline_tasks.values()))
            self.task_manager.update_statistics()

    def _log_event(self, level: str, message: str, module: str = 'UI'):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'module': module,
            'message': message
        }
        if hasattr(self, 'log_viewer'):
            self.log_viewer.add_log(log_entry)

    def _on_simple_pause(self):
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
            try:
                import psutil
                memory_mb = psutil.Process().memory_info().rss / (1024 ** 2)
                self.memory_label.setText(f"Memory: {memory_mb:.1f} MB")
            except:
                pass
            
            # Update advanced mode widgets if active
            if self.advanced_mode:
                if hasattr(self, 'dashboard'):
                    self.dashboard.update_metrics(summary)
                if hasattr(self, 'metrics_viewer'):
                    self.metrics_viewer.update_metrics(summary, metrics.get_domain_stats(), metrics.get_engine_stats())
            
        except Exception as e:
            logger.error("Metrics display failed", extra={"context": {"error": str(e)}})
    
    def _connect_signals(self):
        """Connect signals between components"""
        if self.advanced_mode and hasattr(self, 'task_manager'):
            self.task_manager.task_action_requested.connect(self._handle_task_action)
    
    def _handle_task_action(self, action: str, task_id: str):
        """Handle task manager actions"""
        task = self.pipeline_tasks.get(task_id)
        if not task:
            self._log_event("WARNING", f"Task {task_id} not found", "TaskManager")
            return

        if action == "pause" and task['status'] in ['Pending', 'Running']:
            task['status'] = 'Paused'
            self.simple_paused = True
            self._log_event("INFO", f"Task {task_id} paused", "TaskManager")
        elif action == "resume" and task['status'] == 'Paused':
            task['status'] = 'Pending'
            self.simple_paused = False
            self._log_event("INFO", f"Task {task_id} resumed", "TaskManager")
        elif action == "cancel" and task['status'] not in ['Completed', 'Cancelled']:
            task['status'] = 'Cancelled'
            self._log_event("INFO", f"Task {task_id} cancelled", "TaskManager")
        else:
            self._log_event("WARNING", f"Unsupported action {action} for task {task_id}", "TaskManager")

        self._refresh_task_manager()
        logger.info("Task action requested", extra={"context": {"action": action, "task_id": task_id}})
    
    def closeEvent(self, event):
        """Handle application close"""
        self.update_timer.stop()
        logger.info("Application closed")
        event.accept()



def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Apply custom theme
    apply_stylesheet(app)
    
    # Create and show main window
    window = NexusDownloaderApp()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
