import sqlite3
import os
from pathlib import Path
from PySide6.QtCore import QStandardPaths, QFile, QIODevice  # <-- обов'язково для телефону

class DatabaseConnection:
    _instance = None
    _db_path = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup_database()
        return cls._instance

    def __init__(self):
        pass

    def _get_db_path(self):
        """Правильний шлях для телефону + десктопу"""
        if self._db_path is None:
            # Qt дає правильну папку для додатка на Android/iOS
            data_location = QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation)
            if not data_location:
                data_location = QStandardPaths.writableLocation(QStandardPaths.HomeLocation)

            app_dir = Path(data_location) / "budget_buddy"
            app_dir.mkdir(parents=True, exist_ok=True)

            self._db_path = app_dir / "budget_buddy.db"
            print(f"📁 База буде в: {self._db_path}")
        return self._db_path

    def _setup_database(self):
        try:
            db_path = self._get_db_path()
            self.connection = sqlite3.connect(str(db_path))
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.connection.row_factory = sqlite3.Row

            # === СХЕМА ===
            # Спробуємо спочатку через Qt resources (якщо ти додав .qrc), потім відносні шляхи
            schema_path = None
            possible_paths = [
                ":/database/ProjetBuddySchema.sql",           # Qt resource (найкраще для телефону)
                Path(__file__).parent.parent / "database" / "ProjetBuddySchema.sql",
                Path(__file__).parent.parent.parent / "database" / "ProjetBuddySchema.sql",
                Path.cwd() / "database" / "ProjetBuddySchema.sql",
            ]

            for p in possible_paths:
                if isinstance(p, str) and p.startswith(":/"):  # Qt resource
                    qfile = QFile(p)
                    if qfile.exists():
                        schema_path = p
                        break
                elif isinstance(p, Path) and p.exists():
                    schema_path = str(p)
                    break

            if schema_path is None:
                print("❌ ERROR: Не знайдено ProjetBuddySchema.sql в жодному місці!")
                print("   Додай файл у resources.qrc або скопіюй SQL в код як строку.")
                self.connection = None
                return

            print(f"✅ Знайдено схему: {schema_path}")
            self.execute_sql_file(schema_path)
            print("✅ База і схема створені успішно!")
        except Exception as e:
            print("❌ Помилка при створенні бази:", e)
            self.connection = None

    def execute_sql_file(self, file_path: str):
        """Універсальний метод (звичайний файл + Qt resource)"""
        try:
            if file_path.startswith(":/"):
                # Qt resource
                qfile = QFile(file_path)
                if not qfile.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
                    raise Exception("Не можу відкрити Qt resource")
                sql_script = bytes(qfile.readAll()).decode("utf-8")
                qfile.close()
            else:
                # звичайний файл
                with open(file_path, "r", encoding="utf-8") as f:
                    sql_script = f.read()

            cursor = self.connection.cursor()
            cursor.executescript(sql_script)  # <-- замість ручного split! Надійніше
            self.connection.commit()
            cursor.close()
            print("✅ SQL-файл виконано")
        except sqlite3.Error as err:
            if "already exists" in str(err).lower():
                print("⚠️ Таблиці вже існують (нормально)")
            else:
                print("❌ Помилка SQL:", err)
        except Exception as e:
            print("❌ Помилка читання SQL:", e)

    def get_connection(self):
        if not hasattr(self, 'connection') or self.connection is None:
            print("🔄 Перепідключення до бази...")
            self._setup_database()
        return self.connection

    def close_connection(self):
        if hasattr(self, 'connection') and self.connection:
            self.connection.close()
            self.connection = None