"""Load vector embeddings into pgvector."""

import logging
from typing import Any

from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]

from src.db.postgres_client import db
from src.utils.data_parser import DataParser

logger = logging.getLogger(__name__)


class VectorLoader:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.parser = DataParser()

    def create_vector_extension(self) -> None:
        """Enable pgvector extension and create embeddings table."""
        with db.get_cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS product_embeddings (
                    product_id VARCHAR(10) PRIMARY KEY REFERENCES products(id),
                    description_embedding vector(384)
                );
            """)
        logger.info("pgvector extension and table created")

    def generate_embeddings(self) -> None:
        """Generate embeddings for all product descriptions."""
        products = self.parser.parse_products()
        count = 0

        for _, product in products.iterrows():
            text = f"{product['NAME']} {product['DESCRIPTION']} {' '.join(product['TAGS'])}"
            embedding = self.model.encode(text)
            self._store_embedding(str(product["ID"]), embedding)
            count += 1

        logger.info("Generated and stored %d embeddings", count)
        print(f"Generated {count} product embeddings")

    def _store_embedding(self, product_id: str, embedding: Any) -> None:
        """Store embedding in pgvector."""
        with db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO product_embeddings (product_id, description_embedding)
                VALUES (%s, %s)
                ON CONFLICT (product_id) DO UPDATE
                SET description_embedding = EXCLUDED.description_embedding;
                """,
                (product_id, embedding.tolist()),
            )

    def load_all(self) -> None:
        """Full pipeline: create extension/table and generate all embeddings."""
        print("Setting up pgvector...")
        self.create_vector_extension()

        print("Generating product embeddings...")
        self.generate_embeddings()

        print("Vector data loading complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loader = VectorLoader()
    loader.load_all()
