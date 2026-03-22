import uuid
from .database import DatabaseConnection  # your path


class AccountAndTransactionManager:
    def __init__(self):
        self.db = DatabaseConnection()   # singleton

    # ====================== HELPER METHODS ======================
    def _get_cursor(self, dictionary=False):
        conn = self.db.get_connection()
        return conn.cursor(dictionary=dictionary)

    def _execute_commit(self, query: str, params: tuple = None):
        """Executes query + commit. Returns lastrowid for INSERT"""
        conn = self.db.get_connection()
        cursor = self._get_cursor()
        try:
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.lastrowid
        finally:
            cursor.close()

    def _fetch_one(self, query: str, params: tuple = None):
        """Returns dict (like in your old DBManager)"""
        conn = self.db.get_connection()
        cursor = self._get_cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchone()
        finally:
            cursor.close()

    # ====================== MAIN METHODS ======================
    def create_account(self, user_id: int, initial_balance: float = 0.0) -> int:
        """Creates account (without name — because it's not in your SQL)"""
        query = """
            INSERT INTO accounts (user_id, balance)
            VALUES (%s, %s)
        """
        account_id = self._execute_commit(query, (user_id, float(initial_balance)))

        if initial_balance != 0:
            self.create_transaction(
                user_id=user_id,
                account_id=account_id,
                amount=abs(initial_balance),
                transaction_type="income" if initial_balance > 0 else "expense",
                category="Initial",
                description="Starting balance"
            )
        return account_id

    def create_transaction(self, user_id: int, account_id: int, amount: float,
                           transaction_type: str, category: str = None, description: str = None) -> str:
        """Adds transaction + automatically updates balance"""
        # Check if account belongs to user
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
        self._execute_commit(query, (
            reference, description, float(amount), transaction_type,
            category, sender_id, receiver_id
        ))

        # Update balance
        sign = 1 if transaction_type == "income" else -1
        self._execute_commit(
            "UPDATE accounts SET balance = balance + %s WHERE id = %s",
            (sign * float(amount), account_id)
        )
        return reference

    def get_user_total_balance(self, user_id: int) -> float:
        """Total balance of all user accounts"""
        row = self._fetch_one(
            "SELECT COALESCE(SUM(balance), 0) as total FROM accounts WHERE user_id = %s",
            (user_id,)
        )
        return float(row['total']) if row else 0.0