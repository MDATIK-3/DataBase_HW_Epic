"""Redis connection and utilities for caching, cart, and rate limiting."""

import json
import logging
from typing import Any

import redis as redis_lib  # type: ignore[import-untyped]

from src.config import CACHE_TTL, CART_TTL, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW, REDIS_CONFIG

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self) -> None:
        self.client = redis_lib.Redis(**REDIS_CONFIG)

    # --- JSON Cache ---

    def get_json(self, key: str) -> Any | None:
        """Get JSON data from Redis."""
        data = self.client.get(key)
        return json.loads(data) if data else None

    def set_json(self, key: str, value: Any, ttl: int = CACHE_TTL) -> None:
        """Set JSON data in Redis with TTL."""
        self.client.setex(key, ttl, json.dumps(value, default=str))

    # --- Shopping Cart (Hash with TTL) ---

    def add_to_cart(self, user_id: str, product_id: str, quantity: int) -> None:
        """Add or update an item in user's cart."""
        cart_key = f"cart:{user_id}"
        self.client.hset(cart_key, product_id, quantity)
        self.client.expire(cart_key, CART_TTL)

    def remove_from_cart(self, user_id: str, product_id: str) -> None:
        """Remove an item from user's cart."""
        self.client.hdel(f"cart:{user_id}", product_id)

    def get_cart(self, user_id: str) -> dict[str, int]:
        """Get all items in user's cart."""
        cart = self.client.hgetall(f"cart:{user_id}")
        return {str(k): int(str(v)) for k, v in cart.items()} if cart else {}

    def clear_cart(self, user_id: str) -> None:
        """Clear user's cart."""
        self.client.delete(f"cart:{user_id}")

    def update_cart_item(self, user_id: str, product_id: str, quantity: int) -> None:
        """Update quantity of an item in cart. Remove if quantity <= 0."""
        if quantity <= 0:
            self.remove_from_cart(user_id, product_id)
        else:
            self.add_to_cart(user_id, product_id, quantity)

    # --- Rate Limiting (String counters with TTL) ---

    def rate_limit_check(self, user_id: str, endpoint: str) -> bool:
        """Check if user has exceeded rate limit. Returns True if allowed."""
        key = f"rate_limit:{user_id}:{endpoint}"
        current = self.client.get(key)

        if current is None:
            self.client.setex(key, RATE_LIMIT_WINDOW, 1)
            return True

        if int(str(current)) >= RATE_LIMIT_REQUESTS:
            return False

        self.client.incr(key)
        return True

    def get_rate_limit_remaining(self, user_id: str, endpoint: str) -> int:
        """Get remaining requests in current window."""
        key = f"rate_limit:{user_id}:{endpoint}"
        current = self.client.get(key)
        if current is None:
            return RATE_LIMIT_REQUESTS
        return max(0, RATE_LIMIT_REQUESTS - int(str(current)))

    # --- Product & Search Cache ---

    def cache_product(self, product_id: str, product_data: dict[str, Any], ttl: int = CACHE_TTL) -> None:
        """Cache a product's data."""
        self.set_json(f"product:{product_id}", product_data, ttl)

    def get_cached_product(self, product_id: str) -> dict[str, Any] | None:
        """Get a cached product."""
        return self.get_json(f"product:{product_id}")

    def cache_search_results(self, query: str, results: list[dict[str, Any]], ttl: int = CACHE_TTL) -> None:
        """Cache search results."""
        self.set_json(f"search:{query}", results, ttl)

    def get_cached_search(self, query: str) -> list[dict[str, Any]] | None:
        """Get cached search results."""
        return self.get_json(f"search:{query}")

    # --- Cache Stats ---

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache hit/miss statistics."""
        stats = self.client.hgetall("cache:stats")
        if not stats:
            return {"hits": 0, "misses": 0, "hit_rate": 0.0}
        hits = int(str(stats.get("hits", 0)))
        misses = int(str(stats.get("misses", 0)))
        total = hits + misses
        return {"hits": hits, "misses": misses, "hit_rate": round(hits / total, 4) if total > 0 else 0.0}

    def record_cache_hit(self) -> None:
        self.client.hincrby("cache:stats", "hits", 1)

    def record_cache_miss(self) -> None:
        self.client.hincrby("cache:stats", "misses", 1)


redis_client = RedisClient()
