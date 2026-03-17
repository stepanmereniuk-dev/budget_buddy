import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QLineEdit, QPushButton, QFrame, QMessageBox,
    QStackedWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap   

class LoginPage(QWidget):
    login_success = Signal()         

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setSpacing(20)
        main_layout.addStretch()

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 16px;
                padding: 40px 30px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(18)

        self.icon_label = QLabel()
        self.icon_label.setText("🔑")                 
        self.icon_label.setStyleSheet("font-size: 110px;")
        self.icon_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.icon_label)

        title = QLabel("Login")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #222;")
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setVerticalSpacing(12)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username or email")
        self.username.setMinimumWidth(260)
        form.addRow("Username:", self.username)

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Password")
        form.addRow("Password:", self.password)

        card_layout.addLayout(form)

        # Login button
        self.login_btn = QPushButton("Login")
        self.login_btn.setDefault(True)                  
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.login_btn.clicked.connect(self.attempt_login)
        card_layout.addWidget(self.login_btn)

        main_layout.addWidget(card)
        main_layout.addStretch()

    def attempt_login(self):
        user = self.username.text().strip()
        pw = self.password.text().strip()
        if user and pw:
            self.login_success.emit()         
        else:
            QMessageBox.warning(self, "Error", "Please fill both fields!")


