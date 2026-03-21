from PySide6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QGridLayout, QStackedWidget, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt


class Dashboard(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        # Main Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # 1. TOP HEADER
        self.header = self.create_header()
        self.layout.addWidget(self.header)

        # 2. STACKED WIDGET (The "Pages")
        self.pages_stack = QStackedWidget()
        
        # Create different pages
        self.home_page = self.create_home_page()
        self.transactions_page = self.create_placeholder_page("Transactions History")
        self.profile_page = self.create_placeholder_page("User Settings")

        self.pages_stack.addWidget(self.home_page)
        self.pages_stack.addWidget(self.transactions_page)
        self.pages_stack.addWidget(self.profile_page)

        self.layout.addWidget(self.pages_stack)

        # 3. BOTTOM NAVIGATION BAR
        self.nav_bar = self.create_nav_bar()
        self.layout.addWidget(self.nav_bar)

    def create_header(self):
        header_frame = QFrame()
        header_frame.setFixedHeight(80)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #6A1B9A;
                color: white;
                border-bottom-left-radius: 20px;
                border-bottom-right-radius: 20px;
            }
        """)
        layout = QHBoxLayout(header_frame)
        layout.setContentsMargins(30, 0, 30, 0)

        user_name = getattr(self.main_window, 'current_user_name', 'User')
        welcome = QLabel(f"Hello, {user_name}! 👋")
        welcome.setStyleSheet("font-size: 20px; font-weight: bold;")

        logout_btn = QPushButton("Log Out")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setFixedSize(90, 35)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid white;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.3); }
        """)
        logout_btn.clicked.connect(self.logout)

        layout.addWidget(welcome)
        layout.addStretch()
        layout.addWidget(logout_btn)
        return header_frame

    def create_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)

        grid = QGridLayout()
        grid.setSpacing(20)

        grid.addWidget(self.create_card("Total Balance", "$12,450", "#4CAF50"), 0, 0)
        grid.addWidget(self.create_card("Monthly Expenses", "-$3,280", "#F44336"), 0, 1)
        grid.addWidget(self.create_card("Monthly Income", "+$8,900", "#2196F3"), 1, 0)
        grid.addWidget(self.create_card("Active Goals", "3 Items", "#FF9800"), 1, 1)

        layout.addLayout(grid)
        layout.addStretch()
        return page

    def create_placeholder_page(self, title):
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel(title)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: #666; font-weight: bold;")
        layout.addStretch()
        layout.addWidget(label)
        layout.addStretch()
        return page

    def create_nav_bar(self):
        nav_frame = QFrame()
        nav_frame.setFixedHeight(70)
        nav_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top: 1px solid #DDD;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: #888;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                color: #6A1B9A;
            }
        """)
        
        layout = QHBoxLayout(nav_frame)
        
        self.btn_home = QPushButton("🏠 Home")
        self.btn_trans = QPushButton("📊 Transactions")
        self.btn_profile = QPushButton("👤 Profile")

        # Set Home as active by default
        self.btn_home.setStyleSheet("color: #6A1B9A; border-bottom: 3px solid #6A1B9A;")

        for i, btn in enumerate([self.btn_home, self.btn_trans, self.btn_profile]):
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, index=i: self.switch_page(index))
            layout.addWidget(btn)

        return nav_frame

    def switch_page(self, index):
        self.pages_stack.setCurrentIndex(index)
        
        # Reset all buttons styles
        buttons = [self.btn_home, self.btn_trans, self.btn_profile]
        for i, btn in enumerate(buttons):
            if i == index:
                btn.setStyleSheet("color: #6A1B9A; border-bottom: 3px solid #6A1B9A;")
            else:
                btn.setStyleSheet("color: #888; border: none;")

    def create_card(self, title: str, value: str, color: str):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: #F8F9FA;
                border: 1px solid #EEE;
                border-radius: 20px;
                padding: 15px;
            }}
        """)
        layout = QVBoxLayout(frame)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 14px; color: #777;")
        
        lbl_value = QLabel(value)
        lbl_value.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        return frame

    def logout(self):
        if hasattr(self.main_window, 'stack'):
            self.main_window.stack.setCurrentIndex(0)