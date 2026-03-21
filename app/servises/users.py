import hashlib
import mysql.connector as mysql
from .database import DatabaseConnection


class UserService:
    def __init__(self):
        self.db = DatabaseConnection()  

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    # ====================== CREATE USER ======================
    def create_user(self, first_name: str, last_name: str, email: str, password: str):
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            password_hash = self.hash_password(password)
            query = """
                INSERT INTO users (first_name, last_name, email, password_hash)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (first_name, last_name, email, password_hash))
            conn.commit()
            cursor.close()
            print("User created successfully.")
        except mysql.Error as err:
            print("Error creating user:", err)
            raise

    # ====================== LOGIN / AUTHENTICATION ======================
    def authenticate_user(self, email: str, password: str):
        """Verifies email + password and returns user data or None"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            password_hash = self.hash_password(password)

            query = """
                SELECT id, first_name, last_name, email, created_at 
                FROM users 
                WHERE email = %s AND password_hash = %s
            """
            cursor.execute(query, (email.strip(), password_hash))
            
            user = cursor.fetchone()
            cursor.close()
            return user
        except Exception as err:
            print("Authentication error:", err)
            return None

    # ====================== CRUD USER METHODS ======================
    def get_user_by_id(self, user_id: int):
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            query = "SELECT id, first_name, last_name, email, created_at FROM users WHERE id = %s"
            cursor.execute(query, (user_id,))

            user = cursor.fetchone()
            cursor.close()
            return user

        except mysql.Error as err:
            print("Error fetching user:", err)

    def get_all_users(self):
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)

            query = "SELECT id, first_name, last_name, email, created_at FROM users"
            cursor.execute(query)

            users = cursor.fetchall()
            cursor.close()
            return users

        except mysql.Error as err:
            print("Error fetching users:", err)

    def update_user(self, user_id: int, first_name: str, last_name: str, email: str):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        query = """
        UPDATE users
        SET first_name = %s,
            last_name = %s,
            email = %s
        WHERE id = %s
        """
        cursor.execute(query, (first_name, last_name, email, user_id))
        conn.commit()
        cursor.close()
        print("User updated successfully.")

    def update_password(self, user_id: int, new_password: str):
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            password_hash = self.hash_password(new_password)

            query = "UPDATE users SET password_hash = %s WHERE id = %s"
            cursor.execute(query, (password_hash, user_id))

            conn.commit()
            cursor.close()
            print("Password updated successfully.")

        except mysql.Error as err:
            print("Error updating password:", err)

    def delete_user(self, user_id: int):
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            query = "DELETE FROM users WHERE id = %s"
            cursor.execute(query, (user_id,))

            conn.commit()
            cursor.close()
            print("User deleted successfully.")

        except mysql.Error as err:
            print("Error deleting user:", err)