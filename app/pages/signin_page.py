import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal
import mysql.connector as mysql   

from servises import UserService        
from components import Input, Button


class SigninPage(QWidget):
    register_success = Signal()
    go_to_login = Signal()

    def __init__(self):
        super().__init__()
        self.user_service = UserService()    
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 40, 40, 40)

        # ================== GREETING FRAME ==================
        greeting_frame = QFrame()
        greeting_frame.setStyleSheet("QFrame { background-color: #6A1B9A; border-radius: 20px; }")
        greeting_frame.setMinimumSize(400, 500)

        greeting_layout = QVBoxLayout(greeting_frame)
        greeting_layout.setSpacing(30)
        greeting_layout.setContentsMargins(50, 120, 50, 120)
        greeting_layout.setAlignment(Qt.AlignCenter)

        hello = QLabel("Create Account!")
        hello.setStyleSheet("color: white; font-size: 32px; font-weight: bold;")
        hello.setAlignment(Qt.AlignCenter)

        desc = QLabel("Register with your personal details to use all\nof the platform's features.")
        desc.setStyleSheet("color: white; font-size: 16px;")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)

        greeting_layout.addWidget(hello)
        greeting_layout.addWidget(desc)
        greeting_layout.addStretch()

        # ================== FORM FRAME ==================
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

        title = QLabel("Sign Up")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #333;")
        title.setAlignment(Qt.AlignCenter)

        self.input_name = Input("Full Name").default_input()
        self.input_email = Input("Email").default_input()
        self.input_password = Input("Password").default_input()
        self.input_confirm = Input("Confirm Password").default_input()

        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_confirm.setEchoMode(QLineEdit.EchoMode.Password)

        # ================== NEW PASSWORD REQUIREMENTS TEXT ==================
        self.password_hint = QLabel(
            "The password must be secure. It should contain at least one\n"
            "uppercase letter, one lowercase letter, one special character, one digit,\n"
            "and be at least 10 characters long."
        )
        self.password_hint.setStyleSheet("color: #666666; font-size: 13px; line-height: 1.4;")
        self.password_hint.setWordWrap(True)
        self.password_hint.setAlignment(Qt.AlignCenter)

        button_register = Button("Sign Up").default_button()
        button_register.clicked.connect(self.check_registration)

        switch_label = QLabel(
            "Already have an account? "
            "<a href='login' style='color: #6A1B9A; text-decoration: none;'>Sign In</a>"
        )
        switch_label.setTextFormat(Qt.TextFormat.RichText)
        switch_label.setAlignment(Qt.AlignCenter)
        switch_label.linkActivated.connect(lambda _: self.go_to_login.emit())

        form_layout.addWidget(title)
        form_layout.addWidget(self.input_name)
        form_layout.addWidget(self.input_email)
        form_layout.addWidget(self.input_password)
        form_layout.addWidget(self.input_confirm)
        form_layout.addWidget(self.password_hint)        
        form_layout.addStretch()
        form_layout.addWidget(button_register)
        form_layout.addWidget(switch_label)

        main_layout.addWidget(greeting_frame, 1)
        main_layout.addWidget(form_frame, 1)

        self.setMinimumSize(880, 560)
    def is_valid_password(self, password: str) -> bool:

        if len(password) < 10:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        if not re.search(r'[^A-Za-z0-9]', password):   
            return False
        return True

    def check_registration(self):
        name = self.input_name.text().strip()
        email = self.input_email.text().strip().lower()
        password = self.input_password.text()
        confirm = self.input_confirm.text()

        if not name or not email or not password:
            msg = QMessageBox(self)
            msg.setWindowTitle("Sorry")
            msg.setText("All fields are required!")
            msg.setStyleSheet("color: black;")
            msg.exec()
            return

        if password != confirm:
            msg = QMessageBox(self)
            msg.setWindowTitle("Error")
            msg.setText("Passwords do not match!")
            msg.setStyleSheet("color: black;")
            msg.exec()
            return

        # ← NEW PASSWORD SECURITY CHECK
        if not self.is_valid_password(password):
            msg = QMessageBox(self)
            msg.setWindowTitle("Weak Password")
            msg.setText("Password must be secure. It should contain at least one\n"
                        "uppercase letter, one lowercase letter, one special character, one digit,\n"
                        "and be at least 10 characters long.")
            msg.setStyleSheet("color: black;")
            msg.exec()
            return

        parts = name.split(maxsplit=1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

        try:
            self.user_service.create_user(first_name, last_name, email, password)

            msg = QMessageBox(self)
            msg.setWindowTitle("Success")
            msg.setText("Account created!\nNow you can log in.")
            msg.setStyleSheet("color: black;")
            msg.exec()
            self.input_email.clear()
            self.input_password.clear()
            self.input_confirm.clear()

            self.register_success.emit()
            self.go_to_login.emit()         

        except mysql.Error as err:
            if err.errno == 1062:  
                msg = QMessageBox(self)
                msg.setWindowTitle("Error")
                msg.setText("A user with that email already exists!")
                msg.setStyleSheet("color: black;")
                msg.exec()
            else:
                msg = QMessageBox(self)
                msg.setWindowTitle("Database Error")
                msg.setText(f"Error: {err}")
                msg.setStyleSheet("color: black;")
                msg.exec()
        except Exception as e:
            msg = QMessageBox(self)
            msg.setWindowTitle("Error")
            msg.setText(str(e))
            msg.setStyleSheet("color: black;")
            msg.exec()
