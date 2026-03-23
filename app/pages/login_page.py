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
        self.is_mobile = False
        self.setup_ui()

    def setup_ui(self):
        # Detect screen size
        screen = self.screen()
        if screen:
            screen_width = screen.size().width()
            self.is_mobile = screen_width < 768
        
        # Use vertical layout on mobile, horizontal on desktop
        if self.is_mobile:
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(15, 15, 15, 15)
            main_layout.setSpacing(15)
        else:
            main_layout = QHBoxLayout(self)
            main_layout.setSpacing(20)
            main_layout.setContentsMargins(40, 40, 40, 40)
        
        greeting_frame = QFrame()
        greeting_frame.setStyleSheet("QFrame { background-color: #6A1B9A; border-radius: 20px; }")
        
        if self.is_mobile:
            greeting_frame.setMinimumHeight(200)
        else:
            greeting_frame.setMinimumSize(400, 500)

        greeting_layout = QVBoxLayout(greeting_frame)
        greeting_layout.setSpacing(20 if self.is_mobile else 30)
        greeting_layout.setContentsMargins(20 if self.is_mobile else 50, 30 if self.is_mobile else 120, 20 if self.is_mobile else 50, 30 if self.is_mobile else 120)
        greeting_layout.setAlignment(Qt.AlignCenter)

        hello = QLabel("Hello, Friend!")
        hello.setStyleSheet(f"color: white; font-size: {24 if self.is_mobile else 32}px; font-weight: bold;")
        hello.setAlignment(Qt.AlignCenter)

        desc = QLabel("Register with your personal details to use all\nof the platform's features.")
        desc.setStyleSheet(f"color: white; font-size: {14 if self.is_mobile else 16}px;")
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
        
        if self.is_mobile:
            form_frame.setMinimumHeight(300)
        else:
            form_frame.setMinimumSize(400, 500)

        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(20 if self.is_mobile else 25)
        form_layout.setContentsMargins(20 if self.is_mobile else 50, 30 if self.is_mobile else 60, 20 if self.is_mobile else 50, 30 if self.is_mobile else 60)

        title = QLabel("Sign In")
        title.setStyleSheet(f"font-size: {24 if self.is_mobile else 28}px; font-weight: bold; color: #333;")
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
        switch_label.setStyleSheet(f"font-size: {12 if self.is_mobile else 14}px;")
        switch_label.linkActivated.connect(lambda _: self.go_to_register.emit())

        form_layout.addWidget(title)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(self.password_input)
        form_layout.addStretch()
        form_layout.addWidget(button_login)
        form_layout.addWidget(switch_label)

        main_layout.addWidget(greeting_frame, 1)
        main_layout.addWidget(form_frame, 1)

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
