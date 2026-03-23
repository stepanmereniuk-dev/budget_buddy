import uuid
from .database import DatabaseConnection

class AccountAndTransactionManager:
    def __init__(self):
        self.db = DatabaseConnection()

    def _get_cursor(self, dictionary=False):
        conn = self.db.get_connection()
        return conn.cursor(dictionary=dictionary)

    def _execute_commit(self, query: str, params: tuple = None):
        conn = self.db.get_connection()
        cursor = self._get_cursor()
        try:
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.lastrowid
        finally:
            cursor.close()

    def _fetch_all(self, query: str, params: tuple = None):
        conn = self.db.get_connection()
        cursor = self._get_cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()

    def _fetch_one(self, query: str, params: tuple = None):
        conn = self.db.get_connection()
        cursor = self._get_cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchone()
        finally:
            cursor.close()

    # ====================== NEW METHOD — ALL ACCOUNTS WITH EMAIL ======================
    def get_all_receiver_options(self):
        """Returns ALL accounts with email for receiver selection (for email transfers)."""
        query = """
            SELECT u.email, a.id AS account_id, a.balance 
            FROM users u 
            INNER JOIN accounts a ON u.id = a.user_id 
            ORDER BY u.email, a.id
        """
        return self._fetch_all(query)

    # ====================== ACCOUNTS ======================
    def create_account(self, user_id: int, initial_balance: float = 0.0) -> int:
        query = "INSERT INTO accounts (user_id, balance) VALUES (%s, %s)"
        account_id = self._execute_commit(query, (user_id, float(initial_balance)))
        if initial_balance != 0:
            self.create_transaction(user_id, account_id, abs(initial_balance),
                                    "income" if initial_balance > 0 else "expense",
                                    "Initial", "Starting balance")
        return account_id

    def get_user_accounts(self, user_id: int):
        return self._fetch_all("SELECT id, balance FROM accounts WHERE user_id = %s", (user_id,))

    def has_account(self, user_id: int) -> bool:
        row = self._fetch_one("SELECT 1 FROM accounts WHERE user_id = %s LIMIT 1", (user_id,))
        return bool(row)

    # ====================== TRANSACTIONS (updated — supports receiver without owner check) ======================
    def create_transaction(self, user_id: int | None, account_id: int, amount: float,
                           transaction_type: str, category: str = None, description: str = None) -> str:
        if user_id is not None:
            check = self._fetch_one("SELECT user_id FROM accounts WHERE id = %s", (account_id,))
            if not check or check['user_id'] != user_id:
                raise ValueError("Account does not belong to this user")

        reference = f"txn_{uuid.uuid4().hex[:16]}"
        sender_id = account_id if transaction_type == "expense" else None
        receiver_id = account_id if transaction_type == "income" else None

        query = """
            INSERT INTO transactions (reference, description, amount, transaction_type, 
                                    category, sender_account_id, receiver_account_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        self._execute_commit(query, (reference, description, float(amount), transaction_type,
                                     category, sender_id, receiver_id))

        sign = 1 if transaction_type == "income" else -1
        self._execute_commit("UPDATE accounts SET balance = balance + %s WHERE id = %s",
                             (sign * float(amount), account_id))
        return reference

    def create_transfer(self, sender_account_id: int, receiver_account_id: int, amount: float, user_id: int) -> str:
        if sender_account_id == receiver_account_id:
            raise ValueError("Cannot transfer to the same account")

        # Check sender
        sender = self._fetch_one("SELECT user_id, balance FROM accounts WHERE id = %s", (sender_account_id,))
        if not sender or sender['user_id'] != user_id:
            raise ValueError("Sender account does not belong to you")
        if sender['balance'] < amount:
            raise ValueError("Not enough balance")

        # Check receiver exists
        if not self._fetch_one("SELECT 1 FROM accounts WHERE id = %s", (receiver_account_id,)):
            raise ValueError("Receiver account does not exist")

        # Execute transfer
        self.create_transaction(user_id, sender_account_id, amount, "expense", "Transfer",
                                f"Transfer to account {receiver_account_id}")
        self.create_transaction(None, receiver_account_id, amount, "income", "Transfer",   # None = no owner check
                                f"Transfer from account {sender_account_id}")
        return "Transfer successful"

    def get_user_transactions(self, user_id: int):
        query = """
            SELECT t.created_at, t.description, t.amount, t.transaction_type,
                   t.category, 
                   COALESCE(a_sender.id, '—') as from_account,
                   COALESCE(a_receiver.id, '—') as to_account
            FROM transactions t
            LEFT JOIN accounts a_sender ON t.sender_account_id = a_sender.id
            LEFT JOIN accounts a_receiver ON t.receiver_account_id = a_receiver.id
            WHERE t.sender_account_id IN (SELECT id FROM accounts WHERE user_id = %s)
               OR t.receiver_account_id IN (SELECT id FROM accounts WHERE user_id = %s)
            ORDER BY t.created_at DESC
        """
        return self._fetch_all(query, (user_id, user_id))

    def get_user_total_balance(self, user_id: int) -> float:
        row = self._fetch_one("SELECT COALESCE(SUM(balance), 0) as total FROM accounts WHERE user_id = %s", (user_id,))
        return float(row['total']) if row else 0.0

    # ====================== FILTERED SEARCH ======================
    def search_transactions(self, user_id: int, date_from: str = None, date_to: str = None,
                            category: str = None, transaction_type: str = None,
                            sort_by_amount: str = None) -> list:
        """Search transactions with multiple filters combined.

        Args:
            date_from: 'YYYY-MM-DD' start date
            date_to: 'YYYY-MM-DD' end date
            category: category name filter
            transaction_type: 'income', 'expense', or 'transfer'
            sort_by_amount: 'asc' or 'desc'
        """
        query = """
            SELECT t.created_at, t.description, t.amount, t.transaction_type,
                   t.category,
                   COALESCE(a_sender.id, '—') as from_account,
                   COALESCE(a_receiver.id, '—') as to_account
            FROM transactions t
            LEFT JOIN accounts a_sender ON t.sender_account_id = a_sender.id
            LEFT JOIN accounts a_receiver ON t.receiver_account_id = a_receiver.id
            WHERE (t.sender_account_id IN (SELECT id FROM accounts WHERE user_id = %s)
               OR t.receiver_account_id IN (SELECT id FROM accounts WHERE user_id = %s))
        """
        params = [user_id, user_id]

        if date_from:
            query += " AND DATE(t.created_at) >= %s"
            params.append(date_from)
        if date_to:
            query += " AND DATE(t.created_at) <= %s"
            params.append(date_to)
        if category:
            query += " AND t.category = %s"
            params.append(category)
        if transaction_type:
            if transaction_type.lower() == "transfer":
                query += " AND t.category = 'Transfer'"
            else:
                query += " AND t.transaction_type = %s"
                params.append(transaction_type)

        if sort_by_amount and sort_by_amount.lower() in ('asc', 'desc'):
            query += f" ORDER BY t.amount {sort_by_amount.upper()}"
        else:
            query += " ORDER BY t.created_at DESC"

        return self._fetch_all(query, tuple(params))

    def get_user_categories(self, user_id: int) -> list:
        """Get distinct categories used by this user."""
        query = """
            SELECT DISTINCT t.category FROM transactions t
            WHERE (t.sender_account_id IN (SELECT id FROM accounts WHERE user_id = %s)
               OR t.receiver_account_id IN (SELECT id FROM accounts WHERE user_id = %s))
            AND t.category IS NOT NULL
            ORDER BY t.category
        """
        rows = self._fetch_all(query, (user_id, user_id))
        return [r['category'] for r in rows if r['category']]

    def get_monthly_summary(self, user_id: int) -> list:
        """Get monthly income/expense summary."""
        query = """
            SELECT DATE_FORMAT(t.created_at, '%%Y-%%m') as month,
                   SUM(CASE WHEN t.transaction_type = 'income' THEN t.amount ELSE 0 END) as total_income,
                   SUM(CASE WHEN t.transaction_type = 'expense' THEN t.amount ELSE 0 END) as total_expense
            FROM transactions t
            WHERE t.sender_account_id IN (SELECT id FROM accounts WHERE user_id = %s)
               OR t.receiver_account_id IN (SELECT id FROM accounts WHERE user_id = %s)
            GROUP BY DATE_FORMAT(t.created_at, '%%Y-%%m')
            ORDER BY month DESC
            LIMIT 12
        """
        return self._fetch_all(query, (user_id, user_id))

    def get_category_breakdown(self, user_id: int) -> list:
        """Get expense breakdown by category (for pie/donut chart)."""
        query = """
            SELECT t.category, SUM(t.amount) as total
            FROM transactions t
            WHERE t.transaction_type = 'expense'
              AND t.sender_account_id IN (SELECT id FROM accounts WHERE user_id = %s)
              AND t.category IS NOT NULL
            GROUP BY t.category
            ORDER BY total DESC
        """
        return self._fetch_all(query, (user_id,))