"""
Settings Panel Widget - Application configuration
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, QComboBox,
    QFormLayout, QMessageBox, QFileDialog, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class SettingsPanelWidget(QWidget):
    """Widget for application settings and configuration"""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Tabs for different setting categories
        tabs = QTabWidget()
        
        # Network settings
        network_tab = self._create_network_settings()
        tabs.addTab(network_tab, "🌐 Network")
        
        # Download settings
        download_tab = self._create_download_settings()
        tabs.addTab(download_tab, "⬇️ Downloads")
        
        # Resource settings
        resource_tab = self._create_resource_settings()
        tabs.addTab(resource_tab, "⚙️ Resources")
        
        # Engine settings
        engine_tab = self._create_engine_settings()
        tabs.addTab(engine_tab, "🔧 Engines")
        
        # Logging settings
        logging_tab = self._create_logging_settings()
        tabs.addTab(logging_tab, "📝 Logging")
        
        layout.addWidget(tabs)
        
        # Button bar
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save Settings")
        save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(save_btn)
        
        reset_btn = QPushButton("🔄 Reset to Default")
        reset_btn.clicked.connect(self._reset_settings)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _create_network_settings(self) -> QWidget:
        """Create network settings tab"""
        widget = QWidget()
        layout = QFormLayout()
        
        # Rate limit
        self.rate_limit = QSpinBox()
        self.rate_limit.setMinimum(1)
        self.rate_limit.setMaximum(1000)
        self.rate_limit.setValue(5)
        self.rate_limit.setSuffix(" req/sec")
        layout.addRow("Rate Limit:", self.rate_limit)
        
        # Connection timeout
        self.timeout = QSpinBox()
        self.timeout.setMinimum(5)
        self.timeout.setMaximum(300)
        self.timeout.setValue(30)
        self.timeout.setSuffix(" seconds")
        layout.addRow("Connection Timeout:", self.timeout)
        
        # Max connections
        self.max_connections = QSpinBox()
        self.max_connections.setMinimum(1)
        self.max_connections.setMaximum(1000)
        self.max_connections.setValue(100)
        layout.addRow("Max Connections:", self.max_connections)
        
        # Proxy settings
        self.use_proxy = QCheckBox("Enable Proxy Rotation")
        layout.addRow("Proxy:", self.use_proxy)
        
        widget.setLayout(layout)
        return widget
    
    def _create_download_settings(self) -> QWidget:
        """Create download settings tab"""
        widget = QWidget()
        layout = QFormLayout()
        
        # Download path
        self.download_path = QLineEdit()
        self.download_path.setText("./downloads")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_download_path)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.download_path)
        path_layout.addWidget(browse_btn)
        layout.addRow("Download Path:", path_layout)
        
        # Chunk size
        self.chunk_size = QSpinBox()
        self.chunk_size.setMinimum(1024)
        self.chunk_size.setMaximum(10 * 1024 * 1024)
        self.chunk_size.setValue(1024 * 1024)
        self.chunk_size.setSingleStep(1024)
        self.chunk_size.setSuffix(" bytes")
        layout.addRow("Chunk Size:", self.chunk_size)
        
        # Max retries
        self.max_retries = QSpinBox()
        self.max_retries.setMinimum(0)
        self.max_retries.setMaximum(10)
        self.max_retries.setValue(3)
        layout.addRow("Max Retries:", self.max_retries)
        
        # Bandwidth limit
        self.bandwidth_limit = QSpinBox()
        self.bandwidth_limit.setMinimum(0)
        self.bandwidth_limit.setMaximum(1000)
        self.bandwidth_limit.setValue(0)
        self.bandwidth_limit.setSuffix(" Mbps (0=unlimited)")
        layout.addRow("Bandwidth Limit:", self.bandwidth_limit)
        
        widget.setLayout(layout)
        return widget
    
    def _create_resource_settings(self) -> QWidget:
        """Create resource settings tab"""
        widget = QWidget()
        layout = QFormLayout()
        
        # Max threads
        self.max_threads = QSpinBox()
        self.max_threads.setMinimum(1)
        self.max_threads.setMaximum(64)
        self.max_threads.setValue(8)
        layout.addRow("Max Threads:", self.max_threads)
        
        # Memory limit
        self.memory_limit = QSpinBox()
        self.memory_limit.setMinimum(10)
        self.memory_limit.setMaximum(100)
        self.memory_limit.setValue(85)
        self.memory_limit.setSuffix(" %")
        layout.addRow("Memory Limit:", self.memory_limit)
        
        # Disk space minimum
        self.disk_minimum = QSpinBox()
        self.disk_minimum.setMinimum(1)
        self.disk_minimum.setMaximum(100)
        self.disk_minimum.setValue(2)
        self.disk_minimum.setSuffix(" GB")
        layout.addRow("Min Disk Space:", self.disk_minimum)
        
        # Enable backpressure
        self.enable_backpressure = QCheckBox("Enable Backpressure Throttling")
        self.enable_backpressure.setChecked(True)
        layout.addRow("Backpressure:", self.enable_backpressure)
        
        widget.setLayout(layout)
        return widget
    
    def _create_engine_settings(self) -> QWidget:
        """Create engine settings tab"""
        widget = QWidget()
        layout = QFormLayout()
        
        # Engine selection
        self.default_engine = QComboBox()
        self.default_engine.addItems([
            "fast_engine_v1",
            "spider_engine_v1",
            "stealth_engine_v1",
            "headless_engine_v1",
            "media_engine_v1"
        ])
        layout.addRow("Default Engine:", self.default_engine)
        
        # Enable fallback chain
        self.enable_fallback = QCheckBox("Enable Fallback Chain")
        self.enable_fallback.setChecked(True)
        layout.addRow("Fallback Chain:", self.enable_fallback)
        
        # Engine timeout
        self.engine_timeout = QSpinBox()
        self.engine_timeout.setMinimum(5)
        self.engine_timeout.setMaximum(300)
        self.engine_timeout.setValue(30)
        self.engine_timeout.setSuffix(" seconds")
        layout.addRow("Engine Timeout:", self.engine_timeout)
        
        widget.setLayout(layout)
        return widget
    
    def _create_logging_settings(self) -> QWidget:
        """Create logging settings tab"""
        widget = QWidget()
        layout = QFormLayout()
        
        # Log level
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level.setCurrentText("INFO")
        layout.addRow("Log Level:", self.log_level)
        
        # Enable file logging
        self.file_logging = QCheckBox("Enable File Logging")
        self.file_logging.setChecked(True)
        layout.addRow("File Logging:", self.file_logging)
        
        # Log file location
        self.log_file = QLineEdit()
        self.log_file.setText("./logs/nexus.log")
        layout.addRow("Log File:", self.log_file)
        
        # Max log size
        self.max_log_size = QSpinBox()
        self.max_log_size.setMinimum(1)
        self.max_log_size.setMaximum(1000)
        self.max_log_size.setValue(10)
        self.max_log_size.setSuffix(" MB")
        layout.addRow("Max Log Size:", self.max_log_size)
        
        # JSON logging
        self.json_logging = QCheckBox("Use JSON Format")
        self.json_logging.setChecked(True)
        layout.addRow("JSON Format:", self.json_logging)
        
        widget.setLayout(layout)
        return widget
    
    def _browse_download_path(self):
        """Browse for download path"""
        path = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if path:
            self.download_path.setText(path)
    
    def _save_settings(self):
        """Save settings"""
        # In production, save to config.yaml
        QMessageBox.information(self, "Settings Saved", "Configuration saved successfully!")
    
    def _reset_settings(self):
        """Reset to default settings"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Reset all settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._load_settings()
            QMessageBox.information(self, "Reset Complete", "Settings reset to defaults!")
    
    def _load_settings(self):
        """Load current settings"""
        # In production, load from config.yaml
        pass
