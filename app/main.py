import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QStackedWidget,
    QWidget,
    QVBoxLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor
from pages import LoginPage, SigninPage, Dashboard
from servises import AccountAndTransactionManager


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Budget Buddy")
        
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: white;")
        self.setCentralWidget(central_widget)
        
        self.current_user = None

        vertical_layout = QVBoxLayout(central_widget)

        self.stack = QStackedWidget()

        self.login_page = LoginPage()
        self.signin_page = SigninPage()
        self.dashboard = Dashboard(self)

        
        self.account_service = AccountAndTransactionManager()
        self.dashboard.account_service = self.account_service

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.signin_page)
        self.stack.addWidget(self.dashboard)
        
        vertical_layout.addWidget(self.stack)
        self.stack.setCurrentIndex(0)
        self.login_page.go_to_register.connect(self.switch_to_signin)
        self.signin_page.go_to_login.connect(self.switch_to_login)
        self.login_page.login_success.connect(self.switch_to_dashboard)
        
        self.login_page.login_success.connect(
            lambda user: (self.dashboard.check_create_button_visibility(), self.dashboard.update_balance())
        )

    def switch_to_login(self):
        self.stack.setCurrentIndex(0)

    def switch_to_signin(self):
        self.stack.setCurrentIndex(1)
        
    def switch_to_dashboard(self, user):
        self.current_user = user
        self.stack.setCurrentIndex(2)
        self.dashboard.update_user_info()
        self.dashboard.update_balance()
        self.dashboard.check_create_button_visibility()   


if __name__ == "__main__":
    app = QApplication(sys.argv)
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(255, 255, 255))
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.Button, QColor(255, 255, 255))
    palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    palette.setColor(QPalette.Highlight, QColor(106, 27, 154))   
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    window = App()
    window.showMaximized()
    sys.exit(app.exec())