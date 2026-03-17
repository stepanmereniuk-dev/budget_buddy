from PySide6.QtWidgets import ( QWidget, QFrame, QHBoxLayout, QPushButton)
from PySide6.QtCore import Qt
import sys


class Dashboard:
    def __init__(self, main_window):
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        horisontal_grid = QHBoxLayout()
        styled_frame = QFrame()
        styled_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 16px;
            }
        """)
        login_frame = QFrame()

