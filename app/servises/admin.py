from .database import DatabaseConnection


class AdminService:
    """Service for banker/admin operations — manage client portfolios."""

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

    # ====================== ADMIN CHECK ======================
    def is_admin(self, user_id: int) -> bool:
        """Check if a user is a banker/admin."""
        row = self._fetch_one("SELECT 1 FROM admins WHERE user_id = %s", (user_id,))
        return bool(row)

    def promote_to_admin(self, user_id: int):
        """Promote a regular user to banker/admin."""
        if self.is_admin(user_id):
            raise ValueError("User is already an admin")
        self._execute_commit("INSERT INTO admins (user_id) VALUES (%s)", (user_id,))

    def remove_admin(self, user_id: int):
        """Remove admin/banker role from a user."""
        self._execute_commit("DELETE FROM admins WHERE user_id = %s", (user_id,))

    # ====================== CLIENT PORTFOLIO ======================
    def get_all_clients(self):
        """Get all non-admin users (clients) with their total balance."""
        query = """
            SELECT u.id, u.first_name, u.last_name, u.email, u.created_at,
                   COALESCE(SUM(a.balance), 0) as total_balance,
                   COUNT(a.id) as account_count
            FROM users u
            LEFT JOIN accounts a ON u.id = a.user_id
            WHERE u.id NOT IN (SELECT user_id FROM admins)
            GROUP BY u.id, u.first_name, u.last_name, u.email, u.created_at
            ORDER BY u.last_name, u.first_name
        """
        return self._fetch_all(query)

    def get_client_accounts(self, client_id: int):
        """Get all accounts for a specific client."""
        query = """
            SELECT a.id, a.balance, a.created_at
            FROM accounts a
            WHERE a.user_id = %s
            ORDER BY a.id
        """
        return self._fetch_all(query, (client_id,))

    def get_client_transactions(self, client_id: int):
        """Get all transactions for a specific client."""
        query = """
            SELECT t.created_at, t.description, t.amount, t.transaction_type,
                   t.category, t.reference,
                   COALESCE(a_sender.id, '—') as from_account,
                   COALESCE(a_receiver.id, '—') as to_account
            FROM transactions t
            LEFT JOIN accounts a_sender ON t.sender_account_id = a_sender.id
            LEFT JOIN accounts a_receiver ON t.receiver_account_id = a_receiver.id
            WHERE t.sender_account_id IN (SELECT id FROM accounts WHERE user_id = %s)
               OR t.receiver_account_id IN (SELECT id FROM accounts WHERE user_id = %s)
            ORDER BY t.created_at DESC
        """
        return self._fetch_all(query, (client_id, client_id))

    def get_all_admins(self):
        """Get list of all admins/bankers."""
        query = """
            SELECT u.id, u.first_name, u.last_name, u.email
            FROM users u
            INNER JOIN admins a ON u.id = a.user_id
            ORDER BY u.last_name, u.first_name
        """
        return self._fetch_all(query)

    # ====================== BANKER OPERATIONS ON BEHALF OF CLIENT ======================
    def banker_deposit(self, account_service, client_id: int, account_id: int,
                       amount: float, category: str = "Deposit", description: str = "Banker deposit"):
        """Banker performs a deposit on behalf of a client."""
        # Verify account belongs to client
        check = self._fetch_one("SELECT user_id FROM accounts WHERE id = %s", (account_id,))
        if not check or check['user_id'] != client_id:
            raise ValueError("Account does not belong to this client")
        return account_service.create_transaction(client_id, account_id, amount,
                                                   "income", category, description)

    def banker_withdraw(self, account_service, client_id: int, account_id: int,
                        amount: float, category: str = "Withdrawal", description: str = "Banker withdrawal"):
        """Banker performs a withdrawal on behalf of a client."""
        check = self._fetch_one("SELECT user_id FROM accounts WHERE id = %s", (account_id,))
        if not check or check['user_id'] != client_id:
            raise ValueError("Account does not belong to this client")
        # Check balance
        acc = self._fetch_one("SELECT balance FROM accounts WHERE id = %s", (account_id,))
        if acc['balance'] < amount:
            raise ValueError(f"Insufficient balance (${acc['balance']:,.2f})")
        return account_service.create_transaction(client_id, account_id, amount,
                                                   "expense", category, description)

    def banker_transfer(self, account_service, client_id: int, sender_account_id: int,
                        receiver_account_id: int, amount: float):
        """Banker performs a transfer on behalf of a client."""
        check = self._fetch_one("SELECT user_id FROM accounts WHERE id = %s", (sender_account_id,))
        if not check or check['user_id'] != client_id:
            raise ValueError("Sender account does not belong to this client")
        return account_service.create_transfer(sender_account_id, receiver_account_id, amount, client_id)

    def banker_create_account(self, account_service, client_id: int, initial_balance: float = 0.0):
        """Banker creates a new account for a client."""
        return account_service.create_account(client_id, initial_balance)
