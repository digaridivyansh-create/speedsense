import os
from pathlib import Path

from dotenv import load_dotenv
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env.local")
load_dotenv(BASE_DIR / ".env")


DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured.")


# Reuse PostgreSQL connections instead of creating a new
# Neon connection for every request.
_pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=0,
    max_size=5,
    timeout=10,
    kwargs={
        "row_factory": dict_row
    }
)


class PooledConnection:

    def __init__(self, pool):
        self._pool = pool
        self._connection = pool.getconn()
        self._closed = False

    def __getattr__(self, name):
        return getattr(self._connection, name)

    def close(self):
        if not self._closed:
            self._pool.putconn(self._connection)
            self._closed = True


def get_connection():
    return PooledConnection(_pool)


def initialize_database():

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    title TEXT NOT NULL,
                    amount DOUBLE PRECISION NOT NULL,
                    transaction_type TEXT NOT NULL
                        CHECK(transaction_type IN ('income', 'expense')),
                    category TEXT NOT NULL,
                    transaction_date DATE NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    category TEXT NOT NULL,
                    amount DOUBLE PRECISION NOT NULL,
                    month TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE(user_id, category, month)
                )
            """)

        connection.commit()

    finally:
        connection.close()


initialize_database()
