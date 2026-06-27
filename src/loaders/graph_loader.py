"""Load data into Neo4j graph database."""

import logging

import pandas as pd

from src.db.neo4j_client import neo4j_client
from src.utils.data_parser import DataParser

logger = logging.getLogger(__name__)


class GraphLoader:
    def __init__(self):
        self.parser = DataParser()
        self.client = neo4j_client

    def load_users(self):
        """Load user nodes into Neo4j."""
        users = self.parser.parse_users()

        with self.client.driver.session() as session:
            for _, user in users.iterrows():
                session.run(
                    """
                    MERGE (u:User {id: $id})
                    SET u.name = $name, u.join_date = $join_date
                    """,
                    id=user["ID"],
                    name=user["NAME"],
                    join_date=str(pd.Timestamp(str(user["JOIN_DATE"])).date()),
                )

        logger.info("Loaded %d user nodes", len(users))
        print(f"Loaded {len(users)} user nodes into Neo4j")

    def load_categories(self):
        """Load category nodes into Neo4j."""
        categories = self.parser.parse_categories()

        with self.client.driver.session() as session:
            for _, cat in categories.iterrows():
                session.run(
                    """
                    MERGE (c:Category {id: $id})
                    SET c.name = $name
                    """,
                    id=cat["ID"],
                    name=cat["NAME"],
                )

        logger.info("Loaded %d category nodes", len(categories))
        print(f"Loaded {len(categories)} category nodes into Neo4j")

    def load_products(self):
        """Load product nodes and BELONGS_TO relationships into Neo4j."""
        products = self.parser.parse_products()
        categories = self.parser.parse_categories()
        cat_name_to_id = dict(zip(categories["NAME"], categories["ID"], strict=False))

        with self.client.driver.session() as session:
            for _, product in products.iterrows():
                session.run(
                    """
                    MERGE (p:Product {id: $id})
                    SET p.name = $name, p.category = $category, p.price = $price
                    """,
                    id=product["ID"],
                    name=product["NAME"],
                    category=product["CATEGORY"],
                    price=float(product["PRICE"]),
                )

                cat_id = cat_name_to_id.get(product["CATEGORY"])
                if cat_id:
                    session.run(
                        """
                        MATCH (p:Product {id: $product_id})
                        MATCH (c:Category {id: $category_id})
                        MERGE (p)-[:BELONGS_TO]->(c)
                        """,
                        product_id=product["ID"],
                        category_id=cat_id,
                    )

        logger.info("Loaded %d product nodes with BELONGS_TO relationships", len(products))
        print(f"Loaded {len(products)} product nodes into Neo4j")

    def load_all(self):
        """Load all graph data into Neo4j."""
        print("Creating constraints...")
        self.client.create_constraints()

        print("Loading users...")
        self.load_users()

        print("Loading categories...")
        self.load_categories()

        print("Loading products...")
        self.load_products()

        print("Graph data loading complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loader = GraphLoader()
    loader.load_all()
