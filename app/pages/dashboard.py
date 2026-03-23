from PySide6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QGridLayout, QStackedWidget,
    QInputDialog, QMessageBox, QScrollArea, QComboBox, QDateEdit, QHeaderView
)
from PySide6.QtCore import Qt, QDate

# ====================== FOR GRAPHICS ======================
import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

sns.set_style("whitegrid")

# ====================== CATEGORY PRESETS ======================
CATEGORIES = [
    "Deposit", "Withdrawal", "Transfer", "Loisirs", "Repas",
    "Courses", "Transport", "Loyer", "Salaire", "Freelance",
    "Sante", "Education", "Abonnements", "Cadeaux", "Autre"
]


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
        self.donut_fig = None
        self.donut_canvas = None
        self.monthly_fig = None
        self.monthly_canvas = None
        self.alert_label = None

        # Detect screen size
        screen = self.screen()
        if screen:
            screen_width = screen.size().width()
            self.is_mobile = screen_width < 768
        else:
            self.is_mobile = False

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
        self.overview_page = self.create_overview_page()
        self.profile_page = self.create_placeholder_page("User Settings")

        self.pages_stack.addWidget(self.home_page)
        self.pages_stack.addWidget(self.transactions_page)
        self.pages_stack.addWidget(self.overview_page)
        self.pages_stack.addWidget(self.profile_page)

        self.layout.addWidget(self.pages_stack)

        self.nav_bar = self.create_nav_bar()
        self.layout.addWidget(self.nav_bar)

    # ====================== HEADER ======================
    def create_header(self):
        header_frame = QFrame()
        header_height = 60 if self.is_mobile else 80
        header_frame.setFixedHeight(header_height)
        header_frame.setStyleSheet("""
            QFrame { background-color: #6A1B9A; color: white;
                     border-bottom-left-radius: 20px;
                     border-bottom-right-radius: 20px; }
        """)
        layout = QHBoxLayout(header_frame)
        layout.setContentsMargins(15 if self.is_mobile else 30, 0, 15 if self.is_mobile else 30, 0)

        self.welcome = QLabel("Hello, User!")
        self.welcome.setStyleSheet(f"font-size: {16 if self.is_mobile else 20}px; font-weight: bold;")

        logout_btn = QPushButton("Log Out")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setFixedSize(80 if self.is_mobile else 90, 35)
        logout_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(255,255,255,0.2); color: white;
                          border: 1px solid white; border-radius: 10px; font-weight: bold;
                          font-size: {12 if self.is_mobile else 14}px; }}
            QPushButton:hover {{ background-color: rgba(255,255,255,0.3); }}
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
            self.welcome.setText(f"Hello, {name}!")
        else:
            self.welcome.setText("Hello, User!")

    def update_balance(self):
        if self.account_service and hasattr(self.main_window, 'current_user') and self.main_window.current_user:
            user_id = self.main_window.current_user.get('id')
            total = self.account_service.get_user_total_balance(user_id)
            self.balance_value_label.setText(f"${total:,.2f}")
            # ====================== OVERDRAFT ALERT ======================
            self.check_overdraft_alert(total)
        else:
            self.balance_value_label.setText("$0.00")
            if self.alert_label:
                self.alert_label.setVisible(False)

    def check_overdraft_alert(self, total_balance):
        """Show alert if balance is negative or close to zero."""
        if not self.alert_label:
            return
        if total_balance < 0:
            self.alert_label.setText(
                "ALERT: Your account is in overdraft! "
                f"Balance: ${total_balance:,.2f}"
            )
            self.alert_label.setStyleSheet("""
                QLabel { background-color: #F44336; color: white; padding: 10px;
                         border-radius: 8px; font-weight: bold; font-size: 14px; }
            """)
            self.alert_label.setVisible(True)
        elif total_balance < 100:
            self.alert_label.setText(
                "WARNING: Low balance! "
                f"Only ${total_balance:,.2f} remaining."
            )
            self.alert_label.setStyleSheet("""
                QLabel { background-color: #FF9800; color: white; padding: 10px;
                         border-radius: 8px; font-weight: bold; font-size: 14px; }
            """)
            self.alert_label.setVisible(True)
        else:
            self.alert_label.setVisible(False)

    # ====================== HOME PAGE ======================
    def create_home_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        page = QWidget()
        layout = QVBoxLayout(page)
        m = 15 if self.is_mobile else 30
        layout.setContentsMargins(m, m, m, m)

        # Alert banner
        self.alert_label = QLabel()
        self.alert_label.setVisible(False)
        self.alert_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.alert_label)

        grid = QGridLayout()
        grid.setSpacing(15 if self.is_mobile else 20)

        # Total Balance
        balance_frame, self.balance_value_label = self.create_card("Total Balance", "$0.00", "#4CAF50")
        grid.addWidget(balance_frame, 0, 0, 1, 2)

        # Bar chart
        self.chart_frame = self.create_balance_chart()
        grid.addWidget(self.chart_frame, 1, 0, 1, 1)

        # Donut chart
        self.donut_frame = self.create_donut_chart()
        grid.addWidget(self.donut_frame, 1, 1, 1, 1)

        layout.addLayout(grid)

        # Action buttons
        btn_layout = QVBoxLayout() if self.is_mobile else QHBoxLayout()
        self.create_btn = QPushButton("Create Account")
        self.transfer_btn = QPushButton("Transfer Money")
        self.deposit_btn = QPushButton("Deposit / Withdraw")

        self.create_btn.clicked.connect(self.show_create_account_dialog)
        self.transfer_btn.clicked.connect(self.show_transfer_dialog)
        self.deposit_btn.clicked.connect(self.show_deposit_dialog)

        for btn in (self.create_btn, self.transfer_btn, self.deposit_btn):
            btn.setCursor(Qt.PointingHandCursor)
            fs = 12 if self.is_mobile else 14
            btn.setStyleSheet(f"""
                QPushButton {{ background-color: #6A1B9A; color: white;
                              border-radius: 12px; padding: 12px; font-weight: bold;
                              font-size: {fs}px; }}
                QPushButton:hover {{ background-color: #8E24AA; }}
            """)
            if self.is_mobile:
                btn.setMinimumHeight(45)
            btn_layout.addWidget(btn)

        layout.addLayout(btn_layout)
        layout.addStretch()
        scroll.setWidget(page)
        return scroll

    # ====================== BAR CHART ======================
    def create_balance_chart(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame { background-color: #F8F9FA; border: 1px solid #EEE;
                     border-radius: 20px; padding: 10px; }
        """)
        layout = QVBoxLayout(frame)

        title = QLabel("Balance Change Over Time")
        title.setStyleSheet(f"font-size: {14 if self.is_mobile else 16}px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        fw = 6 if not self.is_mobile else 5
        fh = 3.5 if not self.is_mobile else 2.5
        self.fig = plt.figure(figsize=(fw, fh))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        self.refresh_chart()
        return frame

    # ====================== DONUT CHART (NEW) ======================
    def create_donut_chart(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame { background-color: #F8F9FA; border: 1px solid #EEE;
                     border-radius: 20px; padding: 10px; }
        """)
        layout = QVBoxLayout(frame)

        title = QLabel("Expenses by Category")
        title.setStyleSheet(f"font-size: {14 if self.is_mobile else 16}px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        fw = 5 if not self.is_mobile else 4
        fh = 3.5 if not self.is_mobile else 2.5
        self.donut_fig = plt.figure(figsize=(fw, fh))
        self.donut_canvas = FigureCanvas(self.donut_fig)
        layout.addWidget(self.donut_canvas)

        return frame

    def refresh_donut_chart(self):
        """Refresh the donut/pie chart showing expense categories."""
        if not self.donut_canvas or not self.main_window.current_user:
            return
        if not self.account_service:
            return

        user_id = self.main_window.current_user['id']
        breakdown = self.account_service.get_category_breakdown(user_id)

        self.donut_fig.clear()
        ax = self.donut_fig.add_subplot(111)

        if not breakdown:
            ax.text(0.5, 0.5, "No expenses yet",
                    ha='center', va='center', fontsize=12, color='#888')
            self.donut_canvas.draw()
            return

        labels = [row['category'] for row in breakdown]
        sizes = [float(row['total']) for row in breakdown]
        total = sum(sizes)
        percentages = [f"{(s/total)*100:.1f}%" for s in sizes]

        colors = ['#6A1B9A', '#8E24AA', '#AB47BC', '#CE93D8', '#E1BEE7',
                  '#4CAF50', '#FF9800', '#F44336', '#2196F3', '#607D8B',
                  '#795548', '#9E9E9E', '#CDDC39', '#00BCD4', '#FF5722']

        wedges, texts, autotexts = ax.pie(
            sizes, labels=None, autopct='%1.1f%%',
            colors=colors[:len(sizes)], startangle=90,
            pctdistance=0.75, wedgeprops=dict(width=0.4, edgecolor='white')
        )

        for autotext in autotexts:
            autotext.set_fontsize(8)
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        # Total in center
        ax.text(0, 0, f"${total:,.0f}", ha='center', va='center',
                fontsize=14, fontweight='bold', color='#333')

        ax.legend(
            [f"{l} ({p})" for l, p in zip(labels, percentages)],
            loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8
        )
        ax.set_aspect('equal')
        self.donut_fig.tight_layout()
        self.donut_canvas.draw()

    def refresh_chart(self):
        if not hasattr(self, 'canvas') or not self.main_window.current_user:
            return
        if not self.account_service:
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

        df['change'] = df.apply(
            lambda row: row['amount']
            if str(row.get('transaction_type', '')).lower() in ['income', 'deposit']
            else -row['amount'],
            axis=1
        )

        daily = df.groupby('date')['change'].sum().reset_index()
        daily['cum_balance'] = daily['change'].cumsum()

        colors = ['#4CAF50' if x >= 0 else '#F44336' for x in daily['change']]
        sns.barplot(data=daily, x='date', y='cum_balance', ax=ax, palette=colors, edgecolor='black')

        ax.set_xlabel("Date")
        ax.set_ylabel("Balance ($)")
        ax.set_title("Cumulative Balance")
        ax.grid(True)
        plt.xticks(rotation=45, ha='right')
        self.fig.tight_layout()
        self.canvas.draw()

    # ====================== OVERVIEW PAGE (NEW) ======================
    def create_overview_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        page = QWidget()
        layout = QVBoxLayout(page)
        m = 15 if self.is_mobile else 30
        layout.setContentsMargins(m, m, m, m)
        layout.setSpacing(15)

        title = QLabel("Monthly Overview")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        # Monthly summary chart
        chart_frame = QFrame()
        chart_frame.setStyleSheet("""
            QFrame { background-color: #F8F9FA; border: 1px solid #EEE;
                     border-radius: 20px; padding: 10px; }
        """)
        chart_layout = QVBoxLayout(chart_frame)

        chart_title = QLabel("Income vs Expenses by Month")
        chart_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        chart_layout.addWidget(chart_title)

        self.monthly_fig = plt.figure(figsize=(10, 4))
        self.monthly_canvas = FigureCanvas(self.monthly_fig)
        chart_layout.addWidget(self.monthly_canvas)

        layout.addWidget(chart_frame)

        # Monthly summary table
        self.monthly_table = QTableWidget(0, 4)
        self.monthly_table.setHorizontalHeaderLabels(["Month", "Income", "Expenses", "Net"])
        self.monthly_table.horizontalHeader().setStretchLastSection(True)
        self.monthly_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.monthly_table.setAlternatingRowColors(True)
        self.monthly_table.setMaximumHeight(250)
        self.monthly_table.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.monthly_table)

        layout.addStretch()
        scroll.setWidget(page)
        return scroll

    def refresh_overview(self):
        """Refresh the monthly overview page."""
        if not self.main_window.current_user or not self.account_service:
            return

        user_id = self.main_window.current_user['id']
        summary = self.account_service.get_monthly_summary(user_id)

        # Update monthly chart
        self.monthly_fig.clear()
        ax = self.monthly_fig.add_subplot(111)

        if not summary:
            ax.text(0.5, 0.5, "No data yet", ha='center', va='center',
                    fontsize=14, color='#888')
            self.monthly_canvas.draw()
            self.monthly_table.setRowCount(0)
            return

        months = [row['month'] for row in reversed(summary)]
        incomes = [float(row['total_income']) for row in reversed(summary)]
        expenses = [float(row['total_expense']) for row in reversed(summary)]

        import numpy as np
        x = np.arange(len(months))
        width = 0.35
        bars1 = ax.bar(x - width/2, incomes, width, label='Income', color='#4CAF50')
        bars2 = ax.bar(x + width/2, expenses, width, label='Expenses', color='#F44336')

        ax.set_xlabel('Month')
        ax.set_ylabel('Amount ($)')
        ax.set_title('Income vs Expenses')
        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, axis='y', alpha=0.3)
        self.monthly_fig.tight_layout()
        self.monthly_canvas.draw()

        # Update monthly table
        self.monthly_table.setRowCount(len(summary))
        for i, row in enumerate(summary):
            inc = float(row['total_income'])
            exp = float(row['total_expense'])
            net = inc - exp

            self.monthly_table.setItem(i, 0, QTableWidgetItem(row['month']))

            inc_item = QTableWidgetItem(f"${inc:,.2f}")
            inc_item.setForeground(Qt.darkGreen)
            self.monthly_table.setItem(i, 1, inc_item)

            exp_item = QTableWidgetItem(f"${exp:,.2f}")
            exp_item.setForeground(Qt.red)
            self.monthly_table.setItem(i, 2, exp_item)

            net_item = QTableWidgetItem(f"${net:,.2f}")
            net_item.setForeground(Qt.darkGreen if net >= 0 else Qt.red)
            self.monthly_table.setItem(i, 3, net_item)

    # ====================== TRANSACTIONS PAGE WITH FILTERS ======================
    def create_transactions_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        m = 15 if self.is_mobile else 30
        layout.setContentsMargins(m, m, m, m)

        # ===== FILTER BAR =====
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame { background-color: #F8F9FA; border: 1px solid #EEE;
                     border-radius: 12px; padding: 8px; }
        """)
        filter_layout = QVBoxLayout(filter_frame)

        filter_title = QLabel("Search & Filter")
        filter_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #6A1B9A;")
        filter_layout.addWidget(filter_title)

        # Row 1: Date filters
        date_row = QHBoxLayout()

        date_from_label = QLabel("From:")
        date_from_label.setStyleSheet("font-size: 12px; color: #555;")
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setStyleSheet("font-size: 12px; padding: 5px;")

        date_to_label = QLabel("To:")
        date_to_label.setStyleSheet("font-size: 12px; color: #555;")
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setStyleSheet("font-size: 12px; padding: 5px;")

        date_row.addWidget(date_from_label)
        date_row.addWidget(self.date_from)
        date_row.addWidget(date_to_label)
        date_row.addWidget(self.date_to)
        date_row.addStretch()
        filter_layout.addLayout(date_row)

        # Row 2: Category, Type, Sort
        filter_row = QHBoxLayout()

        cat_label = QLabel("Category:")
        cat_label.setStyleSheet("font-size: 12px; color: #555;")
        self.filter_category = QComboBox()
        self.filter_category.addItem("All categories")
        self.filter_category.addItems(CATEGORIES)
        self.filter_category.setStyleSheet("font-size: 12px; padding: 5px; min-width: 120px;")

        type_label = QLabel("Type:")
        type_label.setStyleSheet("font-size: 12px; color: #555;")
        self.filter_type = QComboBox()
        self.filter_type.addItems(["All types", "Income", "Expense", "Transfer"])
        self.filter_type.setStyleSheet("font-size: 12px; padding: 5px; min-width: 100px;")

        sort_label = QLabel("Sort:")
        sort_label.setStyleSheet("font-size: 12px; color: #555;")
        self.filter_sort = QComboBox()
        self.filter_sort.addItems(["Date (newest)", "Amount ascending", "Amount descending"])
        self.filter_sort.setStyleSheet("font-size: 12px; padding: 5px; min-width: 140px;")

        filter_row.addWidget(cat_label)
        filter_row.addWidget(self.filter_category)
        filter_row.addWidget(type_label)
        filter_row.addWidget(self.filter_type)
        filter_row.addWidget(sort_label)
        filter_row.addWidget(self.filter_sort)
        filter_row.addStretch()
        filter_layout.addLayout(filter_row)

        # Row 3: Buttons
        btn_row = QHBoxLayout()
        search_btn = QPushButton("Search")
        search_btn.setCursor(Qt.PointingHandCursor)
        search_btn.setStyleSheet("""
            QPushButton { background-color: #6A1B9A; color: white; border-radius: 8px;
                          font-size: 13px; font-weight: bold; padding: 8px 20px; }
            QPushButton:hover { background-color: #8E24AA; }
        """)
        search_btn.clicked.connect(self.search_transactions)

        reset_btn = QPushButton("Reset")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.setStyleSheet("""
            QPushButton { background-color: #888; color: white; border-radius: 8px;
                          font-size: 13px; font-weight: bold; padding: 8px 20px; }
            QPushButton:hover { background-color: #666; }
        """)
        reset_btn.clicked.connect(self.reset_filters)

        btn_row.addWidget(search_btn)
        btn_row.addWidget(reset_btn)
        btn_row.addStretch()

        self.result_count_label = QLabel("")
        self.result_count_label.setStyleSheet("font-size: 12px; color: #666;")
        btn_row.addWidget(self.result_count_label)

        filter_layout.addLayout(btn_row)
        layout.addWidget(filter_frame)

        # ===== TRANSACTIONS TABLE =====
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Date", "Description", "Amount", "Type", "Category", "From", "To"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(f"font-size: {11 if self.is_mobile else 12}px;")

        layout.addWidget(self.table)
        return page

    def search_transactions(self):
        """Apply filters and search transactions."""
        if not self.main_window.current_user:
            return
        user_id = self.main_window.current_user['id']

        # Gather filter values
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")

        category = self.filter_category.currentText()
        if category == "All categories":
            category = None

        tx_type = self.filter_type.currentText().lower()
        if tx_type == "all types":
            tx_type = None

        sort_text = self.filter_sort.currentText()
        sort_by = None
        if "ascending" in sort_text:
            sort_by = "asc"
        elif "descending" in sort_text:
            sort_by = "desc"

        txs = self.account_service.search_transactions(
            user_id, date_from=date_from, date_to=date_to,
            category=category, transaction_type=tx_type,
            sort_by_amount=sort_by
        )

        self.populate_table(txs)
        self.result_count_label.setText(f"{len(txs)} transaction(s) found")

    def reset_filters(self):
        """Reset all filters and show all transactions."""
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        self.filter_category.setCurrentIndex(0)
        self.filter_type.setCurrentIndex(0)
        self.filter_sort.setCurrentIndex(0)
        self.load_transactions()

    def load_transactions(self):
        if not self.main_window.current_user:
            return
        user_id = self.main_window.current_user['id']
        txs = self.account_service.get_user_transactions(user_id)
        self.populate_table(txs)
        self.result_count_label.setText(f"{len(txs)} transaction(s)")

    def populate_table(self, txs):
        """Fill the table with transaction data."""
        self.table.setRowCount(len(txs))
        for i, tx in enumerate(txs):
            self.table.setItem(i, 0, QTableWidgetItem(str(tx['created_at'])))
            self.table.setItem(i, 1, QTableWidgetItem(tx['description'] or "—"))

            amount_item = QTableWidgetItem(f"${abs(tx['amount']):,.2f}")
            tx_type = tx['transaction_type'].upper()
            if tx_type == 'INCOME':
                amount_item.setForeground(Qt.darkGreen)
            elif tx_type == 'EXPENSE':
                amount_item.setForeground(Qt.red)
            self.table.setItem(i, 2, amount_item)

            type_item = QTableWidgetItem(tx_type)
            self.table.setItem(i, 3, type_item)
            self.table.setItem(i, 4, QTableWidgetItem(tx.get('category', '') or '—'))
            self.table.setItem(i, 5, QTableWidgetItem(str(tx['from_account'])))
            self.table.setItem(i, 6, QTableWidgetItem(str(tx['to_account'])))

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
            self.refresh_all()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    # ====================== DEPOSIT / WITHDRAW (with category) ======================
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

        # Category selection (predefined list only)
        category_str, ok_cat = QInputDialog.getItem(
            self, "Category", "Select category:", CATEGORIES, 0, False
        )
        if not ok_cat: return

        amount, ok3 = QInputDialog.getDouble(self, "Deposit / Withdraw", "Amount:", 0.0, 0.01, 999999, 2)
        if not ok3: return

        # Description
        desc, ok_desc = QInputDialog.getText(self, "Description", "Description (optional):")
        if not ok_desc:
            desc = type_str

        try:
            if type_str == "Deposit":
                self.account_service.create_transaction(user_id, account_id, amount,
                                                        "income", category_str, desc or "Deposit")
            else:
                self.account_service.create_transaction(user_id, account_id, amount,
                                                        "expense", category_str, desc or "Withdrawal")

            QMessageBox.information(self, "Success", f"{type_str} of ${amount:,.2f} completed!")
            self.refresh_all()
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
                self.refresh_all()
                self.check_create_button_visibility()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def refresh_all(self):
        """Refresh all dashboard data."""
        self.update_balance()
        self.refresh_chart()
        self.refresh_donut_chart()
        if self.pages_stack.currentIndex() == 1:
            self.load_transactions()
        if self.pages_stack.currentIndex() == 2:
            self.refresh_overview()

    def check_create_button_visibility(self):
        if self.main_window.current_user and self.create_btn:
            has = self.account_service.has_account(self.main_window.current_user['id'])
            self.create_btn.setVisible(not has)

    def create_card(self, title: str, value: str, color: str):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{ background-color: #F8F9FA; border: 1px solid #EEE;
                      border-radius: 20px; padding: {10 if self.is_mobile else 15}px; }}
        """)
        layout = QVBoxLayout(frame)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: {12 if self.is_mobile else 14}px; color: #777;")
        lbl_value = QLabel(value)
        lbl_value.setStyleSheet(f"font-size: {20 if self.is_mobile else 24}px; font-weight: bold; color: {color};")
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        return frame, lbl_value

    def create_placeholder_page(self, title):
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel(title)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"font-size: {18 if self.is_mobile else 24}px; color: #666; font-weight: bold;")
        layout.addStretch()
        layout.addWidget(label)
        layout.addStretch()
        return page

    # ====================== NAVBAR (4 tabs now) ======================
    def create_nav_bar(self):
        nav_frame = QFrame()
        nav_height = 60 if self.is_mobile else 70
        nav_frame.setFixedHeight(nav_height)
        nav_frame.setStyleSheet(f"""
            QFrame {{ background-color: white; border-top: 1px solid #DDD; }}
            QPushButton {{ background-color: transparent; border: none; color: #888;
                          font-size: {11 if self.is_mobile else 14}px; font-weight: bold; padding: 10px; }}
            QPushButton:hover {{ color: #6A1B9A; }}
        """)
        layout = QHBoxLayout(nav_frame)
        layout.setSpacing(0)
        layout.setContentsMargins(5 if self.is_mobile else 10, 0, 5 if self.is_mobile else 10, 0)

        self.btn_home = QPushButton("Home")
        self.btn_trans = QPushButton("Transactions")
        self.btn_overview = QPushButton("Overview")
        self.btn_profile = QPushButton("Profile")

        self.btn_home.setStyleSheet(f"color: #6A1B9A; border-bottom: 3px solid #6A1B9A; font-size: {11 if self.is_mobile else 14}px;")

        self.nav_buttons = [self.btn_home, self.btn_trans, self.btn_overview, self.btn_profile]
        for i, btn in enumerate(self.nav_buttons):
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, idx=i: self.switch_page(idx))
            layout.addWidget(btn)

        return nav_frame

    def switch_page(self, index):
        self.pages_stack.setCurrentIndex(index)
        font_size = 11 if self.is_mobile else 14
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.setStyleSheet(f"color: #6A1B9A; border-bottom: 3px solid #6A1B9A; font-size: {font_size}px;")
            else:
                btn.setStyleSheet(f"color: #888; border: none; font-size: {font_size}px;")

        if index == 0:
            self.refresh_chart()
            self.refresh_donut_chart()
        elif index == 1 and self.table:
            self.load_transactions()
        elif index == 2:
            self.refresh_overview()

    def logout(self):
        if hasattr(self.main_window, 'current_user'):
            self.main_window.current_user = None
        self.update_user_info()
        if self.balance_value_label:
            self.balance_value_label.setText("$0.00")
        if self.alert_label:
            self.alert_label.setVisible(False)
        if hasattr(self.main_window, 'stack'):
            self.main_window.stack.setCurrentIndex(0)
