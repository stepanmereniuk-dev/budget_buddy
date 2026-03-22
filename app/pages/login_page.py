import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal

from components import Input, Button
from servises import UserService       


class LoginPage(QWidget):
    login_success = Signal(dict)    
    go_to_register = Signal()

    def __init__(self):
        super().__init__()
        self.user_service = UserService()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 40, 40, 40)
        greeting_frame = QFrame()
        greeting_frame.setStyleSheet("QFrame { background-color: #6A1B9A; border-radius: 20px; }")
        greeting_frame.setMinimumSize(400, 500)

        greeting_layout = QVBoxLayout(greeting_frame)
        greeting_layout.setSpacing(30)
        greeting_layout.setContentsMargins(50, 120, 50, 120)
        greeting_layout.setAlignment(Qt.AlignCenter)

        hello = QLabel("Hello, Friend!")
        hello.setStyleSheet("color: white; font-size: 32px; font-weight: bold;")
        hello.setAlignment(Qt.AlignCenter)

        desc = QLabel("Register with your personal details to use all\nof the platform's features.")
        desc.setStyleSheet("color: white; font-size: 16px;")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)

        greeting_layout.addWidget(hello)
        greeting_layout.addWidget(desc)
        greeting_layout.addStretch()

        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 20px;
            }
        """)
        form_frame.setMinimumSize(400, 500)

        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(25)
        form_layout.setContentsMargins(50, 60, 50, 60)

        title = QLabel("Sign In")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #333;")
        title.setAlignment(Qt.AlignCenter)

        self.email_input = Input("Email").default_input()
        self.password_input = Input("Password").default_input()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        button_login = Button("Sign In").default_button()
        button_login.clicked.connect(self.check_login)

        switch_label = QLabel(
            "Don't have an account? "
            "<a href='register' style='color: #6A1B9A; text-decoration: none;'>Sign Up</a>"
        )
        switch_label.setTextFormat(Qt.TextFormat.RichText)
        switch_label.setAlignment(Qt.AlignCenter)
        switch_label.linkActivated.connect(lambda _: self.go_to_register.emit())

        form_layout.addWidget(title)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(self.password_input)
        form_layout.addStretch()
        form_layout.addWidget(button_login)
        form_layout.addWidget(switch_label)

        main_layout.addWidget(greeting_frame, 1)
        main_layout.addWidget(form_frame, 1)

        self.setMinimumSize(880, 560)

    def check_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()

        if not email or not password:
            msg = QMessageBox(self)
            msg.setWindowTitle("Error")
            msg.setText("Please enter both email and password!")
            msg.setStyleSheet("color: black;")
            msg.exec()
            return
        user = self.user_service.authenticate_user(email, password)

        if user:
            msg = QMessageBox(self)
            msg.setWindowTitle("Success")
            msg.setText(f"Welcome, {user['first_name']} {user['last_name']}!")
            msg.setStyleSheet("color: black;")
            msg.exec()
            self.login_success.emit(user)            
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle("Error")
            msg.setText("Invalid email or password!")
            msg.setStyleSheet("color: black;")
            msg.exec()
