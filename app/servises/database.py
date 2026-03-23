import mysql.connector as mysql

class DatabaseConnection:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup_database()
        return cls._instance

    def _setup_database(self):
        try:
            self.create_database_if_not_exists()
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            schema_path = os.path.join(os.path.dirname(base_dir), "database", "ProjetBuddySchema.sql")
            self.execute_sql_file(schema_path)
            print("Database and schema from schema.sql CREATED successfully.")
        except Exception as e:
            print("Error setting up the database:", e)
            self.connection = None

    def create_database_if_not_exists(self):
        try:
            temp_conn = mysql.connect(
                host="127.0.0.1",
                user="root",
                password="",
            )
            cursor = temp_conn.cursor()
            cursor.execute("SHOW DATABASES LIKE 'budget_buddy_db'")
            if cursor.fetchone() is None:
                print("Database does not exist — creating...")
                cursor.execute("CREATE DATABASE budget_buddy_db")
                print("Database created!")

            cursor.close()
            temp_conn.close()

            self.connection = mysql.connect(
                host="127.0.0.1",
                user="root",
                password="",
                database="budget_buddy_db"
            )
            print("Connected to budget_buddy_db")
            
        except mysql.Error as err:  
            print("Failed to create/connect to the database:", err)
            self.connection = None

    def execute_sql_file(self, file_path: str):
        try:
            cursor = self.connection.cursor()
            with open(file_path, "r", encoding="utf-8") as f:
                sql_script = f.read()
            
            statements = sql_script.split(";")
            for statement in statements:
                stmt = statement.strip()
                if stmt:
                    try:
                        cursor.execute(stmt)
                        print(f"Executed: {stmt[:100]}...")
                    except mysql.Error as err:
                        print("Error in statement:")
                        print(stmt)
                        print("Error:", err)
            
            self.connection.commit()
            cursor.close()
            print("SQL file executed successfully.")
            
        except Exception as e:
            print("Error executing SQL file:", e)

    def get_connection(self):
        if not hasattr(self, 'connection') or not self.connection or not self.connection.is_connected():
            print("Reconnecting to the database...")
            self.connection = mysql.connect(
                host="127.0.0.1",
                user="root",
                password="",
                database="budget_buddy_db"
            )
        return self.connection