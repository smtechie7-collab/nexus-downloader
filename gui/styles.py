"""
Application Styling and Theming
"""

from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtWidgets import QApplication


def apply_stylesheet(app: QApplication):
    """Apply custom stylesheet to the application"""
    
    stylesheet = """
    /* Main Application */
    QMainWindow {
        background-color: #1e1e1e;
        color: #d4d4d4;
    }
    
    /* Tabs */
    QTabWidget::pane {
        border: 1px solid #555;
    }
    
    QTabBar::tab {
        background-color: #2d2d2d;
        color: #d4d4d4;
        padding: 8px 20px;
        border: 1px solid #555;
        border-bottom: none;
        margin-right: 2px;
    }
    
    QTabBar::tab:selected {
        background-color: #1e1e1e;
        color: #61dafb;
        border-bottom: 2px solid #61dafb;
    }
    
    QTabBar::tab:hover {
        background-color: #3d3d3d;
    }
    
    /* Buttons */
    QPushButton {
        background-color: #0d47a1;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 6px 12px;
        font-weight: bold;
    }
    
    QPushButton:hover {
        background-color: #1565c0;
    }
    
    QPushButton:pressed {
        background-color: #0c3aa0;
    }
    
    QPushButton:disabled {
        background-color: #555;
        color: #999;
    }
    
    /* Line Edit */
    QLineEdit {
        background-color: #3d3d3d;
        color: #d4d4d4;
        border: 1px solid #555;
        border-radius: 3px;
        padding: 4px;
        selection-background-color: #0d47a1;
        selection-color: white;
    }
    
    QLineEdit:focus {
        border: 1px solid #61dafb;
    }
    
    /* Combo Box */
    QComboBox {
        background-color: #3d3d3d;
        color: #d4d4d4;
        border: 1px solid #555;
        border-radius: 3px;
        padding: 4px;
    }
    
    QComboBox:focus {
        border: 1px solid #61dafb;
    }
    
    QComboBox::drop-down {
        border: none;
    }
    
    QComboBox::down-arrow {
        image: none;
        width: 10px;
        height: 10px;
    }
    
    /* Spin Box */
    QSpinBox, QDoubleSpinBox {
        background-color: #3d3d3d;
        color: #d4d4d4;
        border: 1px solid #555;
        border-radius: 3px;
        padding: 4px;
    }
    
    QSpinBox:focus, QDoubleSpinBox:focus {
        border: 1px solid #61dafb;
    }
    
    /* Checkboxes */
    QCheckBox {
        color: #d4d4d4;
        spacing: 5px;
    }
    
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
    }
    
    QCheckBox::indicator:unchecked {
        background-color: #3d3d3d;
        border: 1px solid #555;
        border-radius: 2px;
    }
    
    QCheckBox::indicator:checked {
        background-color: #0d47a1;
        border: 1px solid #0d47a1;
        border-radius: 2px;
        image: url('check');
    }
    
    /* Radio Button */
    QRadioButton {
        color: #d4d4d4;
        spacing: 5px;
    }
    
    QRadioButton::indicator {
        width: 16px;
        height: 16px;
        border-radius: 8px;
    }
    
    QRadioButton::indicator:unchecked {
        background-color: #3d3d3d;
        border: 1px solid #555;
    }
    
    QRadioButton::indicator:checked {
        background-color: #0d47a1;
        border: 1px solid #0d47a1;
    }
    
    /* Table Widget */
    QTableWidget {
        background-color: #2b2b2b;
        gridline-color: #555;
        color: #d4d4d4;
    }
    
    QTableWidget::item {
        padding: 4px;
        border-bottom: 1px solid #555;
    }
    
    QTableWidget::item:selected {
        background-color: #0d47a1;
        color: white;
    }
    
    QTableWidget::item:hover {
        background-color: #3d3d3d;
    }
    
    QHeaderView::section {
        background-color: #2d2d2d;
        color: #d4d4d4;
        padding: 4px;
        border: 1px solid #555;
        font-weight: bold;
    }
    
    /* Text Edit */
    QTextEdit {
        background-color: #2b2b2b;
        color: #d4d4d4;
        border: 1px solid #555;
        border-radius: 3px;
    }
    
    QTextEdit:focus {
        border: 1px solid #61dafb;
    }
    
    /* Scrollable Areas */
    QScrollBar:vertical {
        background-color: #1e1e1e;
        width: 12px;
        border: none;
    }
    
    QScrollBar::handle:vertical {
        background-color: #555;
        min-height: 20px;
        border-radius: 6px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #777;
    }
    
    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
        border: none;
        width: 0px;
        height: 0px;
    }
    
    QScrollBar:horizontal {
        background-color: #1e1e1e;
        height: 12px;
        border: none;
    }
    
    QScrollBar::handle:horizontal {
        background-color: #555;
        min-width: 20px;
        border-radius: 6px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background-color: #777;
    }
    
    QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {
        border: none;
        width: 0px;
        height: 0px;
    }
    
    /* Group Box */
    QGroupBox {
        color: #d4d4d4;
        border: 1px solid #555;
        border-radius: 4px;
        margin-top: 10px;
        padding-top: 10px;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 3px 0 3px;
    }
    
    /* Labels */
    QLabel {
        color: #d4d4d4;
    }
    
    /* Status Bar */
    QStatusBar {
        background-color: #2d2d2d;
        color: #d4d4d4;
        border-top: 1px solid #555;
    }
    
    QStatusBar::item {
        border: none;
    }
    
    /* Menu Bar */
    QMenuBar {
        background-color: #2d2d2d;
        color: #d4d4d4;
        border-bottom: 1px solid #555;
    }
    
    QMenuBar::item:selected {
        background-color: #0d47a1;
    }
    
    /* Menu */
    QMenu {
        background-color: #2d2d2d;
        color: #d4d4d4;
        border: 1px solid #555;
    }
    
    QMenu::item:selected {
        background-color: #0d47a1;
    }
    
    QMenu::item:disabled {
        color: #999;
    }
    
    /* Progress Bar */
    QProgressBar {
        background-color: #3d3d3d;
        border: 1px solid #555;
        border-radius: 3px;
        text-align: center;
        color: white;
    }
    
    QProgressBar::chunk {
        background-color: #4CAF50;
        border-radius: 2px;
    }
    
    /* Tool Tip */
    QToolTip {
        background-color: #3d3d3d;
        color: #d4d4d4;
        border: 1px solid #555;
        padding: 3px;
        border-radius: 3px;
    }
    
    /* Dialog */
    QDialog {
        background-color: #1e1e1e;
        color: #d4d4d4;
    }
    
    /* Message Box */
    QMessageBox {
        background-color: #1e1e1e;
    }
    
    QMessageBox QLabel {
        color: #d4d4d4;
    }
    
    /* File Dialog */
    QFileDialog {
        background-color: #1e1e1e;
        color: #d4d4d4;
    }
    
    /* Splitter */
    QSplitter::handle {
        background-color: #555;
        width: 6px;
    }
    
    QSplitter::handle:hover {
        background-color: #777;
    }
    """
    
    app.setStyle('Fusion')
    app.setStyleSheet(stylesheet)


# Color scheme constants
COLORS = {
    "primary": QColor("#0d47a1"),
    "secondary": QColor("#61dafb"),
    "success": QColor("#4CAF50"),
    "error": QColor("#F44336"),
    "warning": QColor("#FF9800"),
    "info": QColor("#2196F3"),
    
    "background_dark": QColor("#1e1e1e"),
    "background_medium": QColor("#2b2b2b"),
    "background_light": QColor("#3d3d3d"),
    
    "text_primary": QColor("#d4d4d4"),
    "text_secondary": QColor("#999"),
    "text_disabled": QColor("#555"),
    
    "border": QColor("#555"),
}


def get_font(size: int = 10, bold: bool = False) -> QFont:
    """Get a configured font"""
    font = QFont("Segoe UI", size)
    font.setBold(bold)
    return font
