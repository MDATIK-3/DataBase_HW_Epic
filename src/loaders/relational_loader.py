"""Load data into PostgreSQL database."""

import logging

import pandas as pd

from src.db.postgres_client import db
from src.utils.data_parser import DataParser

logger = logging.getLogger(__name__)


class RelationalLoader:
    def __init__(self):
        self.db = db
        self.parser = DataParser()

    def load_categories(self):
        """Load categories into PostgreSQL."""
        categories = self.parser.parse_categories()

        with self.db.get_cursor() as cursor:
            for _, row in categories.iterrows():
                query = """
                    INSERT INTO categories (id, name, description)
                    VALUES (%(id)s, %(name)s, %(description)s)
                    ON CONFLICT (id) DO NOTHING;
                """
                cursor.execute(query, {"id": str(row["ID"]), "name": str(row["NAME"]), "description": str(row["DESCRIPTION"])})

        logger.info("Loaded %d categories", len(categories))

    def load_sellers(self):
        """Load sellers into PostgreSQL."""
        sellers = self.parser.parse_sellers()

        with self.db.get_cursor() as cursor:
            for _, row in sellers.iterrows():
                query = """
                    INSERT INTO sellers (id, name, specialty, rating, joined)
                    VALUES (%(id)s, %(name)s, %(specialty)s, %(rating)s, %(joined)s)
                    ON CONFLICT (id) DO NOTHING;
                """
                joined_ts = pd.Timestamp(str(row["JOINED"]))
                cursor.execute(
                    query,
                    {
                        "id": str(row["ID"]),
                        "name": str(row["NAME"]),
                        "specialty": str(row["SPECIALTY"]),
                        "rating": float(row["RATING"]),
                        "joined": joined_ts.date(),
                    },
                )

        logger.info("Loaded %d sellers", len(sellers))

    def load_users(self):
        """Load users into PostgreSQL."""
        users = self.parser.parse_users()

        with self.db.get_cursor() as cursor:
            for _, row in users.iterrows():
                query = """
                    INSERT INTO users (id, name, email, join_date, location, interests)
                    VALUES (%(id)s, %(name)s, %(email)s, %(join_date)s, %(location)s, %(interests)s)
                    ON CONFLICT (id) DO NOTHING;
                """
                join_ts = pd.Timestamp(str(row["JOIN_DATE"]))
                cursor.execute(
                    query,
                    {
                        "id": str(row["ID"]),
                        "name": str(row["NAME"]),
                        "email": str(row["EMAIL"]),
                        "join_date": join_ts.date(),
                        "location": str(row["LOCATION"]),
                        "interests": list(row["INTERESTS"]),
                    },
                )

        logger.info("Loaded %d users", len(users))

    def load_products(self):
        """Load products into PostgreSQL."""
        products = self.parser.parse_products()

        with self.db.get_cursor() as cursor:
            for _, row in products.iterrows():
                query = """
                    INSERT INTO products (id, name, category, price, seller_id, description, tags, stock)
                    VALUES (%(id)s, %(name)s, %(category)s, %(price)s, %(seller_id)s,
                            %(description)s, %(tags)s, %(stock)s)
                    ON CONFLICT (id) DO NOTHING;
                """
                cursor.execute(
                    query,
                    {
                        "id": str(row["ID"]),
                        "name": str(row["NAME"]),
                        "category": str(row["CATEGORY"]),
                        "price": float(row["PRICE"]),
                        "seller_id": str(row["SELLER_ID"]),
                        "description": str(row["DESCRIPTION"]),
                        "tags": list(row["TAGS"]),
                        "stock": int(row["STOCK"]),
                    },
                )

        logger.info("Loaded %d products", len(products))

    def load_all(self):
        """Load all data into PostgreSQL."""
        print("Creating tables...")
        self.db.create_tables()

        print("Loading categories...")
        self.load_categories()

        print("Loading sellers...")
        self.load_sellers()

        print("Loading users...")
        self.load_users()

        print("Loading products...")
        self.load_products()

        print("Relational data loading complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loader = RelationalLoader()
    loader.load_all()
