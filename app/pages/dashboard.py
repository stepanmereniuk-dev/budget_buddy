from PySide6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QGridLayout, QStackedWidget,
    QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt

# ====================== FOR GRAPHICS ======================
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

sns.set_style("whitegrid")


class Dashboard(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.account_service = None
        self.balance_value_label = None
        self.create_btn = None
        self.transfer_btn = None
        self.deposit_btn = None
        self.table = None
        self.fig = None
        self.canvas = None
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.header = self.create_header()
        self.layout.addWidget(self.header)

        self.pages_stack = QStackedWidget()
        self.home_page = self.create_home_page()
        self.transactions_page = self.create_transactions_page()
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

    def update_balance(self):
        if self.account_service and hasattr(self.main_window, 'current_user') and self.main_window.current_user:
            user_id = self.main_window.current_user.get('id')
            total = self.account_service.get_user_total_balance(user_id)
            self.balance_value_label.setText(f"${total:,.2f}")
        else:
            self.balance_value_label.setText("$0.00")

    # ====================== HOME PAGE (ONLY BALANCE + SMALLER GRAPH) ======================
    def create_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)

        grid = QGridLayout()
        grid.setSpacing(20)

        # Total Balance (full width)
        balance_frame, self.balance_value_label = self.create_card("Total Balance", "$0.00", "#4CAF50")
        grid.addWidget(balance_frame, 0, 0, 1, 2)

        # Smaller graph
        self.chart_frame = self.create_balance_chart()
        grid.addWidget(self.chart_frame, 1, 0, 1, 2)

        layout.addLayout(grid)

        # ====================== BUTTONS (now always visible) ======================
        btn_layout = QHBoxLayout()
        self.create_btn = QPushButton("➕ Create Account")
        self.transfer_btn = QPushButton("↔ Transfer Money")
        self.deposit_btn = QPushButton("💰 Deposit / Withdraw")

        self.create_btn.clicked.connect(self.show_create_account_dialog)
        self.transfer_btn.clicked.connect(self.show_transfer_dialog)
        self.deposit_btn.clicked.connect(self.show_deposit_dialog)

        for btn in (self.create_btn, self.transfer_btn, self.deposit_btn):
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

    # ====================== SMALLER BAR CHART ======================
    def create_balance_chart(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame { background-color: #F8F9FA; border: 1px solid #EEE;
                     border-radius: 20px; padding: 10px; }
        """)
        layout = QVBoxLayout(frame)

        title = QLabel("Balance Change Over Time")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        self.fig = plt.figure(figsize=(8, 4))   # small graph
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        self.refresh_chart()
        return frame

    def refresh_chart(self):
        if not hasattr(self, 'canvas') or not self.main_window.current_user:
            return

        user_id = self.main_window.current_user['id']
        txs = self.account_service.get_user_transactions(user_id)

        self.fig.clear()
        ax = self.fig.add_subplot(111)

        if not txs:
            ax.text(0.5, 0.5, "No transactions yet\nCreate an account or make a transaction", 
                    ha='center', va='center', fontsize=12, color='#888')
            self.canvas.draw()
            return

        df = pd.DataFrame(txs)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['date'] = df['created_at'].dt.date

        # Calculate net change
        df['change'] = df.apply(
            lambda row: row['amount'] 
            if str(row.get('transaction_type', '')).lower() in ['income', 'deposit'] 
            else -row['amount'], 
            axis=1
        )

        daily = df.groupby('date')['change'].sum().reset_index()
        daily['cum_balance'] = daily['change'].cumsum()

        # Bars
        colors = ['#4CAF50' if x >= 0 else '#F44336' for x in daily['change']]
        sns.barplot(data=daily, x='date', y='cum_balance', ax=ax, palette=colors, edgecolor='black')

        ax.set_xlabel("Date")
        ax.set_ylabel("Balance ($)")
        ax.set_title("How Balance Changed (Cumulative)")
        ax.grid(True)
        plt.xticks(rotation=45, ha='right')
        self.fig.tight_layout()
        self.canvas.draw()

    # ====================== TRANSFER BY EMAIL ======================
    def show_transfer_dialog(self):
        user_id = self.main_window.current_user['id']
        accounts = self.account_service.get_user_accounts(user_id)
        if not accounts:
            QMessageBox.warning(self, "Error", "You don't have any accounts!")
            return

        sender_items = [f"Account {acc['id']} (${acc['balance']:,.2f})" for acc in accounts]
        sender_str, ok1 = QInputDialog.getItem(self, "Transfer", "Sender:", sender_items, 0, True)
        if not ok1: return
        sender_id = next((acc['id'] for acc in accounts if f"Account {acc['id']} (${acc['balance']:,.2f})" == sender_str), None)
        if sender_id is None: return

        all_options = self.account_service.get_all_receiver_options()
        receiver_items = [f"{opt['email']} (Account {opt['account_id']} - ${opt['balance']:,.2f})" for opt in all_options]
        receiver_str, ok2 = QInputDialog.getItem(self, "Transfer", "Recipient (email):", receiver_items, 0, True)
        if not ok2: return
        receiver_id = next((opt['account_id'] for opt in all_options 
                           if f"{opt['email']} (Account {opt['account_id']} - ${opt['balance']:,.2f})" == receiver_str), None)
        if receiver_id is None: return

        amount, ok3 = QInputDialog.getDouble(self, "Transfer", "Amount:", 0.0, 0.01, 999999, 2)
        if not ok3: return

        try:
            self.account_service.create_transfer(sender_id, receiver_id, amount, user_id)
            QMessageBox.information(self, "Success", f"Transferred ${amount:,.2f}!")
            self.update_balance()
            self.refresh_chart()
            if self.pages_stack.currentIndex() == 1:
                self.load_transactions()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    # ====================== DEPOSIT / WITHDRAW ======================
    def show_deposit_dialog(self):
        user_id = self.main_window.current_user['id']
        accounts = self.account_service.get_user_accounts(user_id)
        if not accounts:
            QMessageBox.warning(self, "Error", "You don't have any accounts!")
            return

        account_items = [f"Account {acc['id']} (${acc['balance']:,.2f})" for acc in accounts]
        account_str, ok1 = QInputDialog.getItem(self, "Deposit / Withdraw", "Select account:", account_items, 0, True)
        if not ok1: return
        account_id = next((acc['id'] for acc in accounts if f"Account {acc['id']} (${acc['balance']:,.2f})" == account_str), None)
        if account_id is None: return

        types = ["Deposit", "Withdraw"]
        type_str, ok2 = QInputDialog.getItem(self, "Deposit / Withdraw", "Type:", types, 0, True)
        if not ok2: return

        amount, ok3 = QInputDialog.getDouble(self, "Deposit / Withdraw", "Amount:", 0.0, 0.01, 999999, 2)
        if not ok3: return

        try:
            if type_str == "Deposit":
                self.account_service.create_transaction(user_id, account_id, amount, "income", "Deposit", "Deposit")
            else:
                self.account_service.create_transaction(user_id, account_id, amount, "expense", "Withdraw", "Withdrawal")

            QMessageBox.information(self, "Success", f"{type_str} of ${amount:,.2f} completed!")
            self.update_balance()
            self.refresh_chart()
            if self.pages_stack.currentIndex() == 1:
                self.load_transactions()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    # ====================== CREATE ACCOUNT ======================
    def show_create_account_dialog(self):
        user_id = self.main_window.current_user['id']
        balance, ok = QInputDialog.getDouble(self, "New Account", "Initial Balance ($):", 0.00)
        if ok:
            try:
                self.account_service.create_account(user_id, balance)
                QMessageBox.information(self, "Success", "Account created!")
                self.update_balance()
                self.refresh_chart()
                self.check_create_button_visibility()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    # ====================== REMAINING (no changes) ======================
    def create_transactions_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Date", "Description", "Amount", "Type", "From", "To"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)

        refresh_btn = QPushButton("🔄 Refresh History")
        refresh_btn.clicked.connect(self.load_transactions)

        layout.addWidget(refresh_btn)
        layout.addWidget(self.table)
        return page

    def load_transactions(self):
        if not self.main_window.current_user:
            return
        user_id = self.main_window.current_user['id']
        txs = self.account_service.get_user_transactions(user_id)
        self.table.setRowCount(len(txs))
        for i, tx in enumerate(txs):
            self.table.setItem(i, 0, QTableWidgetItem(str(tx['created_at'])))
            self.table.setItem(i, 1, QTableWidgetItem(tx['description'] or "—"))
            self.table.setItem(i, 2, QTableWidgetItem(f"${abs(tx['amount']):,.2f}"))
            self.table.setItem(i, 3, QTableWidgetItem(tx['transaction_type'].upper()))
            self.table.setItem(i, 4, QTableWidgetItem(str(tx['from_account'])))
            self.table.setItem(i, 5, QTableWidgetItem(str(tx['to_account'])))

    def check_create_button_visibility(self):
        if self.main_window.current_user and self.create_btn:
            has = self.account_service.has_account(self.main_window.current_user['id'])
            self.create_btn.setVisible(not has)

    def create_card(self, title: str, value: str, color: str):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{ background-color: #F8F9FA; border: 1px solid #EEE;
                      border-radius: 20px; padding: 15px; }}
        """)
        layout = QVBoxLayout(frame)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 14px; color: #777;")
        lbl_value = QLabel(value)
        lbl_value.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        return frame, lbl_value

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
        layout.setSpacing(0)

        self.btn_home = QPushButton("🏠 Home")
        self.btn_trans = QPushButton("📊 Transactions")
        self.btn_profile = QPushButton("👤 Profile")

        self.btn_home.setStyleSheet("color: #6A1B9A; border-bottom: 3px solid #6A1B9A;")

        for i, btn in enumerate([self.btn_home, self.btn_trans, self.btn_profile]):
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, idx=i: self.switch_page(idx))
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

        if index == 0:
            self.refresh_chart()
        elif index == 1 and self.table:
            self.load_transactions()

    def logout(self):
        if hasattr(self.main_window, 'current_user'):
            self.main_window.current_user = None
        self.update_user_info()
        if self.balance_value_label:
            self.balance_value_label.setText("$0.00")
        if hasattr(self.main_window, 'stack'):
            self.main_window.stack.setCurrentIndex(0)