"""
Metrics Viewer Widget - Detailed performance analytics
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QTabWidget, QLabel, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtChart import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PyQt6.QtCore import Qt as QtCore


class MetricsViewerWidget(QWidget):
    """Widget for viewing detailed performance metrics"""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Tab widget for different metric views
        tabs = QTabWidget()
        
        # Domain stats tab
        self.domain_tab = self._create_domain_stats_tab()
        tabs.addTab(self.domain_tab, "📍 Domain Performance")
        
        # Engine stats tab
        self.engine_tab = self._create_engine_stats_tab()
        tabs.addTab(self.engine_tab, "🔧 Engine Performance")
        
        # Error analysis tab
        self.error_tab = self._create_error_analysis_tab()
        tabs.addTab(self.error_tab, "⚠️ Error Analysis")
        
        layout.addWidget(tabs)
        self.setLayout(layout)
    
    def _create_domain_stats_tab(self):
        """Create domain statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Summary stats
        summary_layout = QHBoxLayout()
        summary_layout.addWidget(QLabel("📊 Top performing domains:"))
        summary_layout.addStretch()
        layout.addLayout(summary_layout)
        
        # Domain table
        self.domain_table = QTableWidget()
        self.domain_table.setColumnCount(6)
        self.domain_table.setHorizontalHeaderLabels([
            "Domain", "Requests", "Success Rate", "Avg Latency (ms)",
            "Min Latency", "Max Latency"
        ])
        
        header = self.domain_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Sample data
        sample_data = [
            ["example.com", "1,245", "96.5%", "245.3", "120", "1250"],
            ["youtube.com", "542", "89.2%", "1245.5", "450", "5230"],
            ["vimeo.com", "389", "94.1%", "567.2", "200", "2100"],
        ]
        
        self.domain_table.setRowCount(len(sample_data))
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(value)
                if col > 1:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.domain_table.setItem(row, col, item)
        
        layout.addWidget(self.domain_table)
        widget.setLayout(layout)
        return widget
    
    def _create_engine_stats_tab(self):
        """Create engine statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Summary
        summary_layout = QHBoxLayout()
        summary_layout.addWidget(QLabel("🔧 Engine performance comparison:"))
        summary_layout.addStretch()
        layout.addLayout(summary_layout)
        
        # Engine table
        self.engine_table = QTableWidget()
        self.engine_table.setColumnCount(5)
        self.engine_table.setHorizontalHeaderLabels([
            "Engine", "Requests", "Success Rate", "Avg Time (ms)", "Status"
        ])
        
        header = self.engine_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Sample data
        sample_data = [
            ["fast_engine_v1", "3,250", "97.2%", "234.5", "✓ Active"],
            ["spider_engine_v1", "1,845", "91.3%", "567.8", "✓ Active"],
            ["stealth_engine_v1", "956", "88.7%", "892.3", "✓ Active"],
            ["media_engine_v1", "745", "93.5%", "1245.2", "✓ Active"],
            ["headless_engine_v1", "432", "85.2%", "2145.7", "✓ Active"],
        ]
        
        self.engine_table.setRowCount(len(sample_data))
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(value)
                if col > 1:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 4 and "Active" in value:
                    item.setForeground(QColor(76, 175, 80))
                self.engine_table.setItem(row, col, item)
        
        layout.addWidget(self.engine_table)
        widget.setLayout(layout)
        return widget
    
    def _create_error_analysis_tab(self):
        """Create error analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Summary
        summary_layout = QHBoxLayout()
        summary_layout.addWidget(QLabel("⚠️ Error distribution:"))
        summary_layout.addStretch()
        layout.addLayout(summary_layout)
        
        # Error table
        self.error_table = QTableWidget()
        self.error_table.setColumnCount(4)
        self.error_table.setHorizontalHeaderLabels([
            "Error Type", "Count", "Percentage", "Last Occurrence"
        ])
        
        header = self.error_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Sample data
        sample_data = [
            ["NetworkError", "245", "45.2%", "2 min ago"],
            ["ParseError", "156", "28.8%", "5 min ago"],
            ["AccessDenied", "89", "16.4%", "12 min ago"],
            ["RateLimited", "32", "5.9%", "1 hour ago"],
            ["Timeout", "20", "3.7%", "3 hours ago"],
        ]
        
        self.error_table.setRowCount(len(sample_data))
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(value)
                if col > 1:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 0:
                    item.setForeground(QColor(244, 67, 54))
                self.error_table.setItem(row, col, item)
        
        layout.addWidget(self.error_table)
        widget.setLayout(layout)
        return widget
    
    def update_metrics(self, summary: dict, domain_stats: dict, engine_stats: dict):
        """Update metrics with new data"""
        try:
            # Update domain stats
            domains = list(domain_stats.keys())[:5]  # Top 5
            self.domain_table.setRowCount(len(domains))
            
            for row, domain in enumerate(domains):
                stats = domain_stats.get(domain, {})
                success_rate = (
                    (stats.get('successes', 0) / stats.get('requests', 1) * 100)
                    if stats.get('requests', 0) > 0 else 0
                )
                avg_latency = stats.get('total_latency', 0) / stats.get('requests', 1) if stats.get('requests', 0) > 0 else 0
                
                data = [
                    domain,
                    str(stats.get('requests', 0)),
                    f"{success_rate:.1f}%",
                    f"{avg_latency:.1f}",
                    f"{stats.get('min_latency', 0):.1f}",
                    f"{stats.get('max_latency', 0):.1f}"
                ]
                
                for col, value in enumerate(data):
                    item = QTableWidgetItem(value)
                    if col > 1:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.domain_table.setItem(row, col, item)
            
            # Update engine stats
            engines = list(engine_stats.keys())[:5]  # Top 5
            self.engine_table.setRowCount(len(engines))
            
            for row, engine in enumerate(engines):
                stats = engine_stats.get(engine, {})
                success_rate = (
                    (stats.get('successes', 0) / stats.get('requests', 1) * 100)
                    if stats.get('requests', 0) > 0 else 0
                )
                
                data = [
                    engine,
                    str(stats.get('requests', 0)),
                    f"{success_rate:.1f}%",
                    f"{stats.get('avg_extraction_time', 0):.1f}",
                    "✓ Active"
                ]
                
                for col, value in enumerate(data):
                    item = QTableWidgetItem(value)
                    if col > 1:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if col == 4:
                        item.setForeground(QColor(76, 175, 80))
                    self.engine_table.setItem(row, col, item)
        
        except Exception as e:
            print(f"Metrics update error: {e}")
