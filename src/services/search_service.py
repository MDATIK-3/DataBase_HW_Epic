"""Search service with caching, full-text, and semantic search."""

import logging
from typing import Any

from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]

from src.db.postgres_client import db
from src.db.redis_client import redis_client

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.redis = redis_client

    def search_products(
        self,
        query: str,
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Full-text search with filters and Redis caching."""
        cache_key = f"{query}:{category}:{min_price}:{max_price}:{limit}"
        cached = self.redis.get_cached_search(cache_key)
        if cached is not None:
            self.redis.record_cache_hit()
            logger.info("Cache HIT for search: %s", query)
            return cached

        self.redis.record_cache_miss()
        logger.info("Cache MISS for search: %s", query)

        conditions = ["(p.name ILIKE %s OR p.description ILIKE %s OR %s = ANY(p.tags))"]
        params: list[Any] = [f"%{query}%", f"%{query}%", query.lower()]

        if category:
            conditions.append("p.category = %s")
            params.append(category)
        if min_price is not None:
            conditions.append("p.price >= %s")
            params.append(min_price)
        if max_price is not None:
            conditions.append("p.price <= %s")
            params.append(max_price)

        params.append(limit)

        sql = f"""
            SELECT p.id, p.name, p.category, p.price, p.description, p.tags, p.stock,
                   s.name AS seller_name
            FROM products p
            LEFT JOIN sellers s ON p.seller_id = s.id
            WHERE {" AND ".join(conditions)}
            ORDER BY p.name
            LIMIT %s;
        """

        with db.get_cursor() as cursor:
            cursor.execute(sql, params)
            results = [dict(row) for row in cursor.fetchall()]

        self.redis.cache_search_results(cache_key, results)
        return results

    def semantic_search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search products using vector similarity (pgvector)."""
        cache_key = f"semantic:{query}:{limit}"
        cached = self.redis.get_cached_search(cache_key)
        if cached is not None:
            self.redis.record_cache_hit()
            return cached

        self.redis.record_cache_miss()
        query_embedding = self.model.encode(query)

        with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT p.id, p.name, p.category, p.price, p.description,
                       s.name AS seller_name,
                       1 - (pe.description_embedding <=> %s::vector) AS similarity
                FROM products p
                JOIN product_embeddings pe ON p.id = pe.product_id
                LEFT JOIN sellers s ON p.seller_id = s.id
                ORDER BY pe.description_embedding <=> %s::vector
                LIMIT %s;
                """,
                (query_embedding.tolist(), query_embedding.tolist(), limit),
            )
            results = [dict(row) for row in cursor.fetchall()]

        for r in results:
            if "similarity" in r:
                r["similarity"] = round(float(r["similarity"]), 4)

        self.redis.cache_search_results(cache_key, results)
        return results

    def find_similar_products(self, product_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """Find products similar to a given product using vector embeddings."""
        cache_key = f"similar:{product_id}:{limit}"
        cached = self.redis.get_cached_search(cache_key)
        if cached is not None:
            self.redis.record_cache_hit()
            return cached

        self.redis.record_cache_miss()

        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT description_embedding FROM product_embeddings WHERE product_id = %s",
                (product_id,),
            )
            row = cursor.fetchone()
            if not row:
                return []

            product_embedding = row["description_embedding"]
            cursor.execute(
                """
                SELECT p.id, p.name, p.category, p.price, p.description,
                       s.name AS seller_name,
                       1 - (pe.description_embedding <=> %s::vector) AS similarity
                FROM products p
                JOIN product_embeddings pe ON p.id = pe.product_id
                LEFT JOIN sellers s ON p.seller_id = s.id
                WHERE p.id != %s
                ORDER BY pe.description_embedding <=> %s::vector
                LIMIT %s;
                """,
                (product_embedding, product_id, product_embedding, limit),
            )
            results = [dict(row) for row in cursor.fetchall()]

        for r in results:
            if "similarity" in r:
                r["similarity"] = round(float(r["similarity"]), 4)

        self.redis.cache_search_results(cache_key, results)
        return results
