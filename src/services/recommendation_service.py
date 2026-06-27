"""Recommendation service using Neo4j graph relationships."""

import logging
from typing import Any

from src.db.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)


class RecommendationService:
    def __init__(self):
        self.client = neo4j_client

    def also_bought(self, product_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """Get 'users who bought this also bought' recommendations."""
        return self.client.get_also_bought(product_id, limit)

    def frequently_bought_together(self, product_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """Get products frequently bought together."""
        return self.client.get_frequently_bought_together(product_id, limit)

    def personalized(self, user_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """Get personalized recommendations for a user based on purchase history."""
        return self.client.get_recommendations(user_id, limit)

    def similar_products(self, product_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """Find similar products based on category and co-purchase patterns."""
        return self.client.get_similar_products(product_id, limit)
