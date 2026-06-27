"""PostgreSQL connection and utilities."""

import logging
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

from src.config import POSTGRES_CONFIG

logger = logging.getLogger(__name__)


class PostgresConnection:
    def __init__(self):
        self.config = POSTGRES_CONFIG

    @contextmanager
    def get_cursor(self):
        """Get a database cursor for raw SQL queries."""
        conn = psycopg2.connect(**self.config)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                yield cursor
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def create_tables(self):
        """Create all tables in the database."""
        with self.get_cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id VARCHAR(10) PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sellers (
                    id VARCHAR(10) PRIMARY KEY,
                    name VARCHAR(150) NOT NULL,
                    specialty VARCHAR(200),
                    rating NUMERIC(3, 2) DEFAULT 0.0,
                    joined DATE
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(10) PRIMARY KEY,
                    name VARCHAR(150) NOT NULL,
                    email VARCHAR(200) UNIQUE NOT NULL,
                    join_date DATE,
                    location VARCHAR(200),
                    interests TEXT[]
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id VARCHAR(10) PRIMARY KEY,
                    name VARCHAR(250) NOT NULL,
                    category VARCHAR(100) REFERENCES categories(name),
                    price NUMERIC(10, 2) NOT NULL,
                    seller_id VARCHAR(10) REFERENCES sellers(id),
                    description TEXT,
                    tags TEXT[],
                    stock INTEGER DEFAULT 0
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(10) REFERENCES users(id),
                    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_amount NUMERIC(10, 2) DEFAULT 0.0,
                    status VARCHAR(20) DEFAULT 'completed'
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    id SERIAL PRIMARY KEY,
                    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
                    product_id VARCHAR(10) REFERENCES products(id),
                    quantity INTEGER NOT NULL DEFAULT 1,
                    unit_price NUMERIC(10, 2) NOT NULL
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS product_embeddings (
                    product_id VARCHAR(10) PRIMARY KEY REFERENCES products(id),
                    description_embedding vector(384)
                );
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_seller ON products(seller_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")

            logger.info("All tables and indexes created successfully.")


db = PostgresConnection()
