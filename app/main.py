import sys
# Import matplotlib BEFORE PySide6 to avoid six/dateutil conflict
import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QStackedWidget,
    QWidget,
    QVBoxLayout,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPalette, QColor, QScreen
from pages import LoginPage, SigninPage, Dashboard, AdminPage
from servises import AccountAndTransactionManager, AdminService


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Budget Buddy")

        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: white;")
        self.setCentralWidget(central_widget)

        self.current_user = None

        vertical_layout = QVBoxLayout(central_widget)
        vertical_layout.setContentsMargins(0, 0, 0, 0)
        vertical_layout.setSpacing(0)

        self.stack = QStackedWidget()

        self.login_page = LoginPage()
        self.signin_page = SigninPage()
        self.dashboard = Dashboard(self)
        self.admin_page = AdminPage(self)

        # Services
        self.account_service = AccountAndTransactionManager()
        self.admin_service = AdminService()

        self.dashboard.account_service = self.account_service
        self.admin_page.admin_service = self.admin_service
        self.admin_page.account_service = self.account_service

        # Stack: 0=login, 1=signin, 2=dashboard, 3=admin
        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.signin_page)
        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.admin_page)

        vertical_layout.addWidget(self.stack)
        self.stack.setCurrentIndex(0)

        # Signals
        self.login_page.go_to_register.connect(self.switch_to_signin)
        self.signin_page.go_to_login.connect(self.switch_to_login)
        self.login_page.login_success.connect(self.on_login_success)

        # Set adaptive window size
        self.setup_window_size()

    def setup_window_size(self):
        """Set responsive window size based on screen"""
        screen = self.screen()
        screen_size = screen.size()
        screen_width = screen_size.width()
        screen_height = screen_size.height()

        if screen_width < 768:
            self.setGeometry(0, 0, screen_width, screen_height)
            self.showMaximized()
        else:
            window_width = int(screen_width * 0.9)
            window_height = int(screen_height * 0.9)
            self.setGeometry(screen_width // 2 - window_width // 2,
                           screen_height // 2 - window_height // 2,
                           window_width, window_height)
            self.show()

    def switch_to_login(self):
        self.stack.setCurrentIndex(0)

    def switch_to_signin(self):
        self.stack.setCurrentIndex(1)

    def on_login_success(self, user):
        """Route to admin page or regular dashboard based on role."""
        self.current_user = user
        user_id = user.get('id')

        if self.admin_service.is_admin(user_id):
            # Banker/Admin → admin dashboard
            self.stack.setCurrentIndex(3)
            self.admin_page.update_header_info()
            self.admin_page.load_clients()
        else:
            # Regular user → normal dashboard
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
    sys.exit(app.exec())
