from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, 
    QHBoxLayout, QPushButton
)
from PySide6.QtCore import Qt
import sys

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Budget buddy")

        central_widget = QWidget()
        central_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 16px;
            }
        """
        )
        horisontal_grid = QHBoxLayout()
        horisontal_grid.setSpacing(20)          
        horisontal_grid.setContentsMargins(40, 40, 40, 40)
        
        styled_frame = QFrame()
        styled_frame.setStyleSheet("""
            QFrame {
                background-color: green;
                border-radius: 16px;
            }
        """)
        
        login_frame = QFrame()
        login_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 16px;
            }
        """)
        
        
        
        styled_frame.setMinimumSize(300, 400)
        login_frame.setMinimumSize(400, 500)
        
        horisontal_grid.addWidget(styled_frame)
        horisontal_grid.addWidget(login_frame)
        central_widget.setLayout(horisontal_grid)
    
        self.setCentralWidget(central_widget)
        self.setMinimumSize(800, 600)


app = QApplication(sys.argv)
window = App()
window.showMaximized()
sys.exit(app.exec())