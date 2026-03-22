from PySide6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QGridLayout, QStackedWidget,
    QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt


class Dashboard(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.account_service = None
        self.balance_value_label = None
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.header = self.create_header()
        self.layout.addWidget(self.header)

        self.pages_stack = QStackedWidget()
        self.home_page = self.create_home_page()
        self.transactions_page = self.create_placeholder_page("Transactions History")
        self.profile_page = self.create_placeholder_page("User Settings")

        self.pages_stack.addWidget(self.home_page)
        self.pages_stack.addWidget(self.transactions_page)
        self.pages_stack.addWidget(self.profile_page)

        self.layout.addWidget(self.pages_stack)

        self.nav_bar = self.create_nav_bar()
        self.layout.addWidget(self.nav_bar)

    # ====================== HEADER ======================
    def create_header(self):
        header_frame = QFrame()
        header_frame.setFixedHeight(80)
        header_frame.setStyleSheet("""
            QFrame { background-color: #6A1B9A; color: white;
                     border-bottom-left-radius: 20px;
                     border-bottom-right-radius: 20px; }
        """)
        layout = QHBoxLayout(header_frame)
        layout.setContentsMargins(30, 0, 30, 0)

        self.welcome = QLabel("Hello, User! 👋")
        self.welcome.setStyleSheet("font-size: 20px; font-weight: bold;")

        logout_btn = QPushButton("Log Out")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setFixedSize(90, 35)
        logout_btn.setStyleSheet("""
            QPushButton { background-color: rgba(255,255,255,0.2); color: white;
                          border: 1px solid white; border-radius: 10px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(255,255,255,0.3); }
        """)
        logout_btn.clicked.connect(self.logout)

        layout.addWidget(self.welcome)
        layout.addStretch()
        layout.addWidget(logout_btn)
        return header_frame

    def update_user_info(self):
        if hasattr(self.main_window, 'current_user') and self.main_window.current_user:
            user = self.main_window.current_user
            name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            self.welcome.setText(f"Hello, {name}! 👋")
        else:
            self.welcome.setText("Hello, User! 👋")

    # ====================== BALANCE ======================
    def update_balance(self):
        if (self.account_service and 
            hasattr(self.main_window, 'current_user') and 
            self.main_window.current_user):
            user_id = self.main_window.current_user.get('id')
            total = self.account_service.get_user_total_balance(user_id)
            self.balance_value_label.setText(f"${total:,.2f}")
        else:
            self.balance_value_label.setText("$0.00")

    # ====================== HOME PAGE (FIXED!) ======================
    def create_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)

        grid = QGridLayout()
        grid.setSpacing(20)

        # Total Balance — keep label for updating
        balance_frame, self.balance_value_label = self.create_card(
            "Total Balance", "$0.00", "#4CAF50"
        )
        grid.addWidget(balance_frame, 0, 0)

        # Other cards — unpack tuple
        expenses_frame, _ = self.create_card("Monthly Expenses", "-$3,280", "#F44336")
        grid.addWidget(expenses_frame, 0, 1)

        income_frame, _ = self.create_card("Monthly Income", "+$8,900", "#2196F3")
        grid.addWidget(income_frame, 1, 0)

        goals_frame, _ = self.create_card("Active Goals", "3 Items", "#FF9800")
        grid.addWidget(goals_frame, 1, 1)

        layout.addLayout(grid)

        # Buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("➕ Create Account")
        deposit_btn = QPushButton("💰 Deposit / Withdraw")

        create_btn.clicked.connect(self.show_create_account_dialog)
        deposit_btn.clicked.connect(self.show_deposit_dialog)

        for btn in (create_btn, deposit_btn):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { background-color: #6A1B9A; color: white;
                              border-radius: 12px; padding: 12px; font-weight: bold; }
                QPushButton:hover { background-color: #8E24AA; }
            """)
            btn_layout.addWidget(btn)

        layout.addLayout(btn_layout)
        layout.addStretch()
        return page

    # ====================== DIALOGS ======================
    def show_create_account_dialog(self):
        if not self.main_window.current_user:
            return
        user_id = self.main_window.current_user['id']

        balance, ok = QInputDialog.getDouble(self, "New Account", "Initial Balance ($):", 0.00, -999999, 999999, 2)
        if ok:
            try:
                self.account_service.create_account(user_id, balance)
                msg = QMessageBox(self)
                msg.setWindowTitle("Success")
                msg.setText("Account created!")
                msg.setStyleSheet("color: black;")
                msg.exec()
                self.update_balance()
            except Exception as e:
                msg = QMessageBox(self)
                msg.setWindowTitle("Error")
                msg.setText(str(e))
                msg.setStyleSheet("color: black;")
                msg.exec()

    def show_deposit_dialog(self):
        if not self.main_window.current_user:
            return
        user_id = self.main_window.current_user['id']

        row = self.account_service._fetch_one("SELECT id FROM accounts WHERE user_id = %s LIMIT 1", (user_id,))
        if not row:
            msg = QMessageBox(self)
            msg.setWindowTitle("No Accounts")
            msg.setText("Create an account first!")
            msg.setStyleSheet("color: black;")
            msg.exec()
            return

        account_id = row['id']

        amount, ok = QInputDialog.getDouble(self, "Deposit / Withdrawal",
                                            "Amount (positive = deposit, negative = withdrawal):",
                                            0.0, -1000000, 1000000, 2)
        if not ok or amount == 0:
            return

        try:
            trans_type = "income" if amount > 0 else "expense"
            self.account_service.create_transaction(
                user_id=user_id,
                account_id=account_id,
                amount=abs(amount),
                transaction_type=trans_type,
                category="Manual",
                description="Balance adjustment"
            )
            msg = QMessageBox(self)
            msg.setWindowTitle("Success")
            msg.setText("Balance updated!")
            msg.setStyleSheet("color: black;")
            msg.exec()
            self.update_balance()
        except Exception as e:
            msg = QMessageBox(self)
            msg.setWindowTitle("Error")
            msg.setText(str(e))
            msg.setStyleSheet("color: black;")
            msg.exec()

    # ====================== CARD ======================
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

        return frame, lbl_value   # return tuple (needed only for Total Balance)

    # ====================== OTHER METHODS (unchanged) ======================
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
            QFrame { background-color: white; border-top: 1px solid #DDD; }
            QPushButton { background-color: transparent; border: none; color: #888;
                          font-size: 14px; font-weight: bold; padding: 10px; }
            QPushButton:hover { color: #6A1B9A; }
        """)
        layout = QHBoxLayout(nav_frame)

        self.btn_home = QPushButton("🏠 Home")
        self.btn_trans = QPushButton("📊 Transactions")
        self.btn_profile = QPushButton("👤 Profile")

        self.btn_home.setStyleSheet("color: #6A1B9A; border-bottom: 3px solid #6A1B9A;")

        for i, btn in enumerate([self.btn_home, self.btn_trans, self.btn_profile]):
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, index=i: self.switch_page(index))
            layout.addWidget(btn)

        return nav_frame

    def switch_page(self, index):
        self.pages_stack.setCurrentIndex(index)
        buttons = [self.btn_home, self.btn_trans, self.btn_profile]
        for i, btn in enumerate(buttons):
            if i == index:
                btn.setStyleSheet("color: #6A1B9A; border-bottom: 3px solid #6A1B9A;")
            else:
                btn.setStyleSheet("color: #888; border: none;")

    def logout(self):
        if hasattr(self.main_window, 'current_user'):
            self.main_window.current_user = None
        self.update_user_info()
        if self.balance_value_label:
            self.balance_value_label.setText("$0.00")
        if hasattr(self.main_window, 'stack'):
            self.main_window.stack.setCurrentIndex(0)