from PySide6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QStackedWidget, QComboBox, QHeaderView,
    QInputDialog, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt


CATEGORIES = [
    "Deposit", "Withdrawal", "Transfer", "Loisirs", "Repas",
    "Courses", "Transport", "Loyer", "Salaire", "Freelance",
    "Sante", "Education", "Abonnements", "Cadeaux", "Autre"
]


class AdminPage(QWidget):
    """Banker/Admin dashboard — manage client portfolios and perform operations."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.admin_service = None
        self.account_service = None
        self.selected_client = None

        screen = self.screen()
        self.is_mobile = screen and screen.size().width() < 768

        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Header
        self.header = self.create_header()
        self.main_layout.addWidget(self.header)

        # Content stack: client list vs client detail
        self.content_stack = QStackedWidget()
        self.client_list_page = self.create_client_list_page()
        self.client_detail_page = self.create_client_detail_page()
        self.content_stack.addWidget(self.client_list_page)
        self.content_stack.addWidget(self.client_detail_page)
        self.main_layout.addWidget(self.content_stack)

    # ====================== HEADER ======================
    def create_header(self):
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("""
            QFrame { background-color: #4A148C; color: white;
                     border-bottom-left-radius: 20px;
                     border-bottom-right-radius: 20px; }
        """)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 0, 30, 0)

        self.header_label = QLabel("Banker Dashboard")
        self.header_label.setStyleSheet("font-size: 20px; font-weight: bold;")

        logout_btn = QPushButton("Log Out")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setFixedSize(90, 35)
        logout_btn.setStyleSheet("""
            QPushButton { background-color: rgba(255,255,255,0.2); color: white;
                          border: 1px solid white; border-radius: 10px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(255,255,255,0.3); }
        """)
        logout_btn.clicked.connect(self.logout)

        layout.addWidget(self.header_label)
        layout.addStretch()
        layout.addWidget(logout_btn)
        return header

    def update_header_info(self):
        if hasattr(self.main_window, 'current_user') and self.main_window.current_user:
            user = self.main_window.current_user
            name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            self.header_label.setText(f"Banker Dashboard — {name}")

    # ====================== CLIENT LIST PAGE ======================
    def create_client_list_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("Client Portfolio")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #333;")
        title_row.addWidget(title)
        title_row.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton { background-color: #4A148C; color: white; border-radius: 8px;
                          font-size: 13px; font-weight: bold; padding: 8px 20px; }
            QPushButton:hover { background-color: #6A1B9A; }
        """)
        refresh_btn.clicked.connect(self.load_clients)
        title_row.addWidget(refresh_btn)
        layout.addLayout(title_row)

        # Stats row
        self.stats_frame = QFrame()
        self.stats_frame.setStyleSheet("""
            QFrame { background-color: #F3E5F5; border-radius: 12px; padding: 10px; }
        """)
        stats_layout = QHBoxLayout(self.stats_frame)
        self.total_clients_label = QLabel("Clients: 0")
        self.total_clients_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4A148C;")
        self.total_balance_label = QLabel("Total managed: $0.00")
        self.total_balance_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4A148C;")
        stats_layout.addWidget(self.total_clients_label)
        stats_layout.addStretch()
        stats_layout.addWidget(self.total_balance_label)
        layout.addWidget(self.stats_frame)

        # Client table
        self.client_table = QTableWidget(0, 6)
        self.client_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Email", "Accounts", "Total Balance", "Actions"]
        )
        self.client_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.client_table.setAlternatingRowColors(True)
        self.client_table.setStyleSheet("font-size: 13px;")
        self.client_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.client_table)

        scroll.setWidget(page)
        return scroll

    def load_clients(self):
        """Load all clients into the table."""
        if not self.admin_service:
            return
        clients = self.admin_service.get_all_clients()

        self.client_table.setRowCount(len(clients))
        total_managed = 0

        for i, client in enumerate(clients):
            balance = float(client['total_balance'])
            total_managed += balance

            self.client_table.setItem(i, 0, QTableWidgetItem(str(client['id'])))

            name = f"{client['first_name']} {client['last_name']}"
            self.client_table.setItem(i, 1, QTableWidgetItem(name))
            self.client_table.setItem(i, 2, QTableWidgetItem(client['email']))
            self.client_table.setItem(i, 3, QTableWidgetItem(str(client['account_count'])))

            bal_item = QTableWidgetItem(f"${balance:,.2f}")
            bal_item.setForeground(Qt.darkGreen if balance >= 0 else Qt.red)
            self.client_table.setItem(i, 4, bal_item)

            # Action button
            manage_btn = QPushButton("Manage")
            manage_btn.setCursor(Qt.PointingHandCursor)
            manage_btn.setStyleSheet("""
                QPushButton { background-color: #6A1B9A; color: white; border-radius: 6px;
                              font-size: 12px; font-weight: bold; padding: 5px 15px; }
                QPushButton:hover { background-color: #8E24AA; }
            """)
            client_data = dict(client)
            manage_btn.clicked.connect(lambda checked=False, c=client_data: self.open_client_detail(c))
            self.client_table.setCellWidget(i, 5, manage_btn)

        self.total_clients_label.setText(f"Clients: {len(clients)}")
        self.total_balance_label.setText(f"Total managed: ${total_managed:,.2f}")

    # ====================== CLIENT DETAIL PAGE ======================
    def create_client_detail_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        # Back button + client info
        top_row = QHBoxLayout()
        back_btn = QPushButton("< Back to clients")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #6A1B9A;
                          font-size: 14px; font-weight: bold; border: none; }
            QPushButton:hover { color: #8E24AA; }
        """)
        back_btn.clicked.connect(self.go_back_to_list)
        top_row.addWidget(back_btn)
        top_row.addStretch()
        layout.addLayout(top_row)

        # Client info card
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame { background-color: #F3E5F5; border-radius: 12px; padding: 15px; }
        """)
        info_layout = QVBoxLayout(info_frame)
        self.client_name_label = QLabel("Client: —")
        self.client_name_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #4A148C;")
        self.client_email_label = QLabel("Email: —")
        self.client_email_label.setStyleSheet("font-size: 14px; color: #666;")
        self.client_balance_label = QLabel("Balance: $0.00")
        self.client_balance_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        info_layout.addWidget(self.client_name_label)
        info_layout.addWidget(self.client_email_label)
        info_layout.addWidget(self.client_balance_label)
        layout.addWidget(info_frame)

        # Action buttons
        action_row = QHBoxLayout()
        actions = [
            ("Deposit", self.banker_deposit),
            ("Withdraw", self.banker_withdraw),
            ("Transfer", self.banker_transfer),
            ("Create Account", self.banker_create_account),
        ]
        for label, callback in actions:
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { background-color: #4A148C; color: white; border-radius: 10px;
                              font-size: 13px; font-weight: bold; padding: 10px 20px; }
                QPushButton:hover { background-color: #6A1B9A; }
            """)
            btn.clicked.connect(callback)
            action_row.addWidget(btn)
        layout.addLayout(action_row)

        # Accounts table
        accounts_label = QLabel("Accounts")
        accounts_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(accounts_label)

        self.accounts_table = QTableWidget(0, 3)
        self.accounts_table.setHorizontalHeaderLabels(["Account ID", "Balance", "Created"])
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.accounts_table.setAlternatingRowColors(True)
        self.accounts_table.setMaximumHeight(150)
        self.accounts_table.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.accounts_table)

        # Transactions table
        tx_label = QLabel("Transaction History")
        tx_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(tx_label)

        self.detail_tx_table = QTableWidget(0, 6)
        self.detail_tx_table.setHorizontalHeaderLabels(
            ["Date", "Description", "Amount", "Type", "Category", "Reference"]
        )
        self.detail_tx_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.detail_tx_table.setAlternatingRowColors(True)
        self.detail_tx_table.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.detail_tx_table)

        scroll.setWidget(page)
        return scroll

    def open_client_detail(self, client):
        """Open detail view for a specific client."""
        self.selected_client = client
        client_id = client['id']
        name = f"{client['first_name']} {client['last_name']}"
        self.client_name_label.setText(f"Client: {name}")
        self.client_email_label.setText(f"Email: {client['email']}")

        # Load accounts
        accounts = self.admin_service.get_client_accounts(client_id)
        total = sum(float(a['balance']) for a in accounts)
        self.client_balance_label.setText(f"Balance: ${total:,.2f}")
        if total < 0:
            self.client_balance_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #F44336;")
        else:
            self.client_balance_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")

        self.accounts_table.setRowCount(len(accounts))
        for i, acc in enumerate(accounts):
            self.accounts_table.setItem(i, 0, QTableWidgetItem(str(acc['id'])))
            bal_item = QTableWidgetItem(f"${float(acc['balance']):,.2f}")
            bal_item.setForeground(Qt.darkGreen if float(acc['balance']) >= 0 else Qt.red)
            self.accounts_table.setItem(i, 1, bal_item)
            self.accounts_table.setItem(i, 2, QTableWidgetItem(str(acc['created_at'])))

        # Load transactions
        txs = self.admin_service.get_client_transactions(client_id)
        self.detail_tx_table.setRowCount(len(txs))
        for i, tx in enumerate(txs):
            self.detail_tx_table.setItem(i, 0, QTableWidgetItem(str(tx['created_at'])))
            self.detail_tx_table.setItem(i, 1, QTableWidgetItem(tx['description'] or '—'))
            amount_item = QTableWidgetItem(f"${abs(tx['amount']):,.2f}")
            tx_type = tx['transaction_type'].upper()
            if tx_type == 'INCOME':
                amount_item.setForeground(Qt.darkGreen)
            elif tx_type == 'EXPENSE':
                amount_item.setForeground(Qt.red)
            self.detail_tx_table.setItem(i, 2, amount_item)
            self.detail_tx_table.setItem(i, 3, QTableWidgetItem(tx_type))
            self.detail_tx_table.setItem(i, 4, QTableWidgetItem(tx.get('category', '') or '—'))
            self.detail_tx_table.setItem(i, 5, QTableWidgetItem(tx.get('reference', '')))

        self.content_stack.setCurrentIndex(1)

    def go_back_to_list(self):
        self.selected_client = None
        self.content_stack.setCurrentIndex(0)
        self.load_clients()

    # ====================== BANKER OPERATIONS ======================
    def _get_client_accounts_items(self):
        """Get account list for dialogs."""
        if not self.selected_client:
            return [], []
        accounts = self.admin_service.get_client_accounts(self.selected_client['id'])
        items = [f"Account {a['id']} (${float(a['balance']):,.2f})" for a in accounts]
        return accounts, items

    def banker_deposit(self):
        if not self.selected_client:
            return
        accounts, items = self._get_client_accounts_items()
        if not accounts:
            QMessageBox.warning(self, "Error", "This client has no accounts!")
            return

        acc_str, ok1 = QInputDialog.getItem(self, "Deposit for client", "Select account:", items, 0, True)
        if not ok1: return
        acc_id = next((a['id'] for a in accounts if f"Account {a['id']} (${float(a['balance']):,.2f})" == acc_str), None)
        if acc_id is None: return

        cat, ok_cat = QInputDialog.getItem(self, "Category", "Select category:", CATEGORIES, 0, False)
        if not ok_cat: return

        amount, ok2 = QInputDialog.getDouble(self, "Deposit", "Amount:", 0.0, 0.01, 999999, 2)
        if not ok2: return

        desc, ok3 = QInputDialog.getText(self, "Description", "Description:")
        if not ok3: desc = "Banker deposit"

        try:
            self.admin_service.banker_deposit(
                self.account_service, self.selected_client['id'], acc_id, amount, cat, desc or "Banker deposit"
            )
            QMessageBox.information(self, "Success", f"Deposited ${amount:,.2f} for client!")
            self.open_client_detail(self.selected_client)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def banker_withdraw(self):
        if not self.selected_client:
            return
        accounts, items = self._get_client_accounts_items()
        if not accounts:
            QMessageBox.warning(self, "Error", "This client has no accounts!")
            return

        acc_str, ok1 = QInputDialog.getItem(self, "Withdraw for client", "Select account:", items, 0, True)
        if not ok1: return
        acc_id = next((a['id'] for a in accounts if f"Account {a['id']} (${float(a['balance']):,.2f})" == acc_str), None)
        if acc_id is None: return

        cat, ok_cat = QInputDialog.getItem(self, "Category", "Select category:", CATEGORIES, 0, False)
        if not ok_cat: return

        amount, ok2 = QInputDialog.getDouble(self, "Withdraw", "Amount:", 0.0, 0.01, 999999, 2)
        if not ok2: return

        desc, ok3 = QInputDialog.getText(self, "Description", "Description:")
        if not ok3: desc = "Banker withdrawal"

        try:
            self.admin_service.banker_withdraw(
                self.account_service, self.selected_client['id'], acc_id, amount, cat, desc or "Banker withdrawal"
            )
            QMessageBox.information(self, "Success", f"Withdrew ${amount:,.2f} for client!")
            self.open_client_detail(self.selected_client)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def banker_transfer(self):
        if not self.selected_client:
            return
        accounts, items = self._get_client_accounts_items()
        if not accounts:
            QMessageBox.warning(self, "Error", "This client has no accounts!")
            return

        sender_str, ok1 = QInputDialog.getItem(self, "Transfer for client", "Sender account:", items, 0, True)
        if not ok1: return
        sender_id = next((a['id'] for a in accounts if f"Account {a['id']} (${float(a['balance']):,.2f})" == sender_str), None)
        if sender_id is None: return

        all_options = self.account_service.get_all_receiver_options()
        recv_items = [f"{o['email']} (Account {o['account_id']} - ${float(o['balance']):,.2f})" for o in all_options]
        recv_str, ok2 = QInputDialog.getItem(self, "Transfer", "Recipient:", recv_items, 0, True)
        if not ok2: return
        recv_id = next((o['account_id'] for o in all_options
                        if f"{o['email']} (Account {o['account_id']} - ${float(o['balance']):,.2f})" == recv_str), None)
        if recv_id is None: return

        amount, ok3 = QInputDialog.getDouble(self, "Transfer", "Amount:", 0.0, 0.01, 999999, 2)
        if not ok3: return

        try:
            self.admin_service.banker_transfer(
                self.account_service, self.selected_client['id'], sender_id, recv_id, amount
            )
            QMessageBox.information(self, "Success", f"Transferred ${amount:,.2f} for client!")
            self.open_client_detail(self.selected_client)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def banker_create_account(self):
        if not self.selected_client:
            return
        balance, ok = QInputDialog.getDouble(self, "New Account for client", "Initial Balance ($):", 0.00)
        if not ok: return

        try:
            self.admin_service.banker_create_account(
                self.account_service, self.selected_client['id'], balance
            )
            QMessageBox.information(self, "Success", "Account created for client!")
            self.open_client_detail(self.selected_client)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def logout(self):
        if hasattr(self.main_window, 'current_user'):
            self.main_window.current_user = None
        if hasattr(self.main_window, 'stack'):
            self.main_window.stack.setCurrentIndex(0)
