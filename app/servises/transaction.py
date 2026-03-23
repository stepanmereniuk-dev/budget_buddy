import uuid
import sqlite3
from .database import DatabaseConnection

class AccountAndTransactionManager:
    def __init__(self):
        self.db = DatabaseConnection()

    # Internal helpers – use SQLite's row_factory (already set in DatabaseConnection)
    def _get_cursor(self):
        conn = self.db.get_connection()
        # No dictionary argument; row_factory = sqlite3.Row is already set on the connection
        return conn.cursor()

    def _execute_commit(self, query: str, params: tuple = None):
        conn = self.db.get_connection()
        cursor = self._get_cursor()
        try:
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.lastrowid   # works in sqlite3
        finally:
            cursor.close()

    def _fetch_all(self, query: str, params: tuple = None):
        conn = self.db.get_connection()
        cursor = self._get_cursor()
        try:
            cursor.execute(query, params or ())
            rows = cursor.fetchall()
            # Return list of dict-like Row objects (each supports .keys(), indexing by name)
            return rows
        finally:
            cursor.close()

    def _fetch_one(self, query: str, params: tuple = None):
        conn = self.db.get_connection()
        cursor = self._get_cursor()
        try:
            cursor.execute(query, params or ())
            row = cursor.fetchone()
            return row   # sqlite3.Row or None
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
        query = "INSERT INTO accounts (user_id, balance) VALUES (?, ?)"
        account_id = self._execute_commit(query, (user_id, float(initial_balance)))
        if initial_balance != 0:
            self.create_transaction(user_id, account_id, abs(initial_balance),
                                    "income" if initial_balance > 0 else "expense",
                                    "Initial", "Starting balance")
        return account_id

    def get_user_accounts(self, user_id: int):
        return self._fetch_all("SELECT id, balance FROM accounts WHERE user_id = ?", (user_id,))

    def has_account(self, user_id: int) -> bool:
        row = self._fetch_one("SELECT 1 FROM accounts WHERE user_id = ? LIMIT 1", (user_id,))
        return bool(row)

    # ====================== TRANSACTIONS ======================
    def create_transaction(self, user_id: int | None, account_id: int, amount: float,
                           transaction_type: str, category: str = None, description: str = None) -> str:
        # If user_id is provided, ensure account belongs to that user
        if user_id is not None:
            check = self._fetch_one("SELECT user_id FROM accounts WHERE id = ?", (account_id,))
            if not check or check['user_id'] != user_id:
                raise ValueError("Account does not belong to this user")

        reference = f"txn_{uuid.uuid4().hex[:16]}"
        sender_id = account_id if transaction_type == "expense" else None
        receiver_id = account_id if transaction_type == "income" else None

        query = """
            INSERT INTO transactions (reference, description, amount, transaction_type, 
                                    category, sender_account_id, receiver_account_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self._execute_commit(query, (reference, description, float(amount), transaction_type,
                                     category, sender_id, receiver_id))

        # Update account balance
        sign = 1 if transaction_type == "income" else -1
        self._execute_commit("UPDATE accounts SET balance = balance + ? WHERE id = ?",
                             (sign * float(amount), account_id))
        return reference

    def create_transfer(self, sender_account_id: int, receiver_account_id: int, amount: float, user_id: int) -> str:
        if sender_account_id == receiver_account_id:
            raise ValueError("Cannot transfer to the same account")

        # Check sender
        sender = self._fetch_one("SELECT user_id, balance FROM accounts WHERE id = ?", (sender_account_id,))
        if not sender or sender['user_id'] != user_id:
            raise ValueError("Sender account does not belong to you")
        if sender['balance'] < amount:
            raise ValueError("Not enough balance")

        # Check receiver exists
        if not self._fetch_one("SELECT 1 FROM accounts WHERE id = ?", (receiver_account_id,)):
            raise ValueError("Receiver account does not exist")

        # Execute transfer
        self.create_transaction(user_id, sender_account_id, amount, "expense", "Transfer",
                                f"Transfer to account {receiver_account_id}")
        self.create_transaction(None, receiver_account_id, amount, "income", "Transfer",
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
            WHERE t.sender_account_id IN (SELECT id FROM accounts WHERE user_id = ?)
               OR t.receiver_account_id IN (SELECT id FROM accounts WHERE user_id = ?)
            ORDER BY t.created_at DESC
        """
        return self._fetch_all(query, (user_id, user_id))

    def get_user_total_balance(self, user_id: int) -> float:
        row = self._fetch_one("SELECT COALESCE(SUM(balance), 0) as total FROM accounts WHERE user_id = ?", (user_id,))
        return float(row['total']) if row else 0.0