import sqlite3
from pathlib import Path
from datetime import datetime


DATABASE_PATH = Path(__file__).parent / "aim_database.db"


class Database:
    def __init__(self, database_path=DATABASE_PATH):
        self.database_path = str(database_path)
        self.initialize()

    def connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self):
        with self.connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS businesses (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    business_type TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id TEXT PRIMARY KEY,
                    business_id TEXT NOT NULL,
                    name TEXT,
                    phone TEXT,
                    status TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (business_id) REFERENCES businesses(id)
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    business_id TEXT NOT NULL,
                    customer_id TEXT,
                    channel TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (business_id) REFERENCES businesses(id),
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS catalog_items (
                    id TEXT PRIMARY KEY,
                    business_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    data TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (business_id) REFERENCES businesses(id)
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    business_id TEXT NOT NULL,
                    customer_id TEXT,
                    status TEXT,
                    data TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (business_id) REFERENCES businesses(id),
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id TEXT PRIMARY KEY,
                    business_id TEXT NOT NULL,
                    customer_id TEXT,
                    status TEXT,
                    interest_score INTEGER,
                    data TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (business_id) REFERENCES businesses(id),
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            """)

            connection.commit()

    def execute(self, query, parameters=()):
        with self.connect() as connection:
            cursor = connection.execute(query, parameters)
            connection.commit()
            return cursor

    def fetch_one(self, query, parameters=()):
        with self.connect() as connection:
            cursor = connection.execute(query, parameters)
            return cursor.fetchone()

    def fetch_all(self, query, parameters=()):
        with self.connect() as connection:
            cursor = connection.execute(query, parameters)
            return cursor.fetchall()


def utc_now():
    return datetime.utcnow().isoformat()


if __name__ == "__main__":
    database = Database()
    print("Database initialized successfully.")
    print(f"Database path: {database.database_path}")