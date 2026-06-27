"""Neo4j connection and utilities."""

import logging
from typing import Any

from neo4j import GraphDatabase  # type: ignore[import-untyped]

from src.config import NEO4J_CONFIG

logger = logging.getLogger(__name__)


class Neo4jClient:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_CONFIG["uri"], auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"])
        )

    def close(self):
        self.driver.close()

    def create_constraints(self):
        """Create uniqueness constraints."""
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
            session.run("CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE")
            session.run("CREATE CONSTRAINT category_id IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE")
        logger.info("Neo4j constraints created")

    def add_purchase(self, user_id: str, product_id: str, quantity: int, date: str):
        """Add a PURCHASED relationship between user and product."""
        with self.driver.session() as session:
            session.run(
                """
                MATCH (u:User {id: $user_id})
                MATCH (p:Product {id: $product_id})
                MERGE (u)-[r:PURCHASED]->(p)
                SET r.quantity = $quantity, r.date = $date
                """,
                user_id=user_id,
                product_id=product_id,
                quantity=quantity,
                date=date,
            )

    def get_also_bought(self, product_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """Users who bought this also bought..."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Product {id: $product_id})<-[:PURCHASED]-(u:User)-[:PURCHASED]->(other:Product)
                WHERE other.id <> $product_id
                WITH other, COUNT(DISTINCT u) AS buyer_count
                ORDER BY buyer_count DESC
                LIMIT $limit
                RETURN other.id AS id, other.name AS name, other.price AS price, buyer_count
                """,
                product_id=product_id,
                limit=limit,
            )
            return [dict(record) for record in result]

    def get_frequently_bought_together(self, product_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """Products frequently bought together with a given product."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Product {id: $product_id})<-[:PURCHASED]-(u:User)-[:PURCHASED]->(other:Product)
                WHERE other.id <> $product_id
                WITH other, COUNT(u) AS co_purchases
                ORDER BY co_purchases DESC
                LIMIT $limit
                RETURN other.id AS id, other.name AS name, other.price AS price,
                       other.category AS category, co_purchases
                """,
                product_id=product_id,
                limit=limit,
            )
            return [dict(record) for record in result]

    def get_recommendations(self, user_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """Personalized recommendations based on purchase history and category affinity."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {id: $user_id})-[:PURCHASED]->(p:Product)-[:BELONGS_TO]->(c:Category)
                WITH u, c, COUNT(p) AS category_affinity
                ORDER BY category_affinity DESC
                WITH u, COLLECT(c)[..3] AS top_categories
                UNWIND top_categories AS tc
                MATCH (tc)<-[:BELONGS_TO]-(rec:Product)
                WHERE NOT (u)-[:PURCHASED]->(rec)
                WITH rec, COUNT(*) AS score
                ORDER BY score DESC
                LIMIT $limit
                RETURN rec.id AS id, rec.name AS name, rec.price AS price,
                       rec.category AS category, score
                """,
                user_id=user_id,
                limit=limit,
            )
            return [dict(record) for record in result]

    def get_similar_products(self, product_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """Find similar products based on shared category and co-purchase patterns."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Product {id: $product_id})-[:BELONGS_TO]->(c:Category)<-[:BELONGS_TO]-(similar:Product)
                WHERE similar.id <> $product_id
                OPTIONAL MATCH (p)<-[:PURCHASED]-(u:User)-[:PURCHASED]->(similar)
                WITH similar, COUNT(DISTINCT u) AS shared_buyers
                ORDER BY shared_buyers DESC
                LIMIT $limit
                RETURN similar.id AS id, similar.name AS name, similar.price AS price,
                       similar.category AS category, shared_buyers
                """,
                product_id=product_id,
                limit=limit,
            )
            return [dict(record) for record in result]


neo4j_client = Neo4jClient()
