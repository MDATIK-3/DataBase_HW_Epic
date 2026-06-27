"""Shopping cart service using Redis with PostgreSQL checkout."""

import logging
from typing import Any

from src.db.postgres_client import db
from src.db.redis_client import redis_client

logger = logging.getLogger(__name__)


class CartService:
    def __init__(self):
        self.redis = redis_client

    def add_item(self, user_id: str, product_id: str, quantity: int = 1) -> dict[str, Any]:
        """Add an item to the user's cart."""
        product = self._get_product_info(product_id)
        if not product:
            return {"error": f"Product {product_id} not found"}
        if product["stock"] < quantity:
            return {"error": f"Insufficient stock for {product_id}"}

        self.redis.add_to_cart(user_id, product_id, quantity)
        return {"status": "added", "product": product["name"], "quantity": quantity}

    def remove_item(self, user_id: str, product_id: str) -> dict[str, str]:
        """Remove an item from user's cart."""
        self.redis.remove_from_cart(user_id, product_id)
        return {"status": "removed", "product_id": product_id}

    def update_quantity(self, user_id: str, product_id: str, quantity: int) -> dict[str, Any]:
        """Update quantity of an item in cart."""
        if quantity <= 0:
            return self.remove_item(user_id, product_id)
        self.redis.update_cart_item(user_id, product_id, quantity)
        return {"status": "updated", "product_id": product_id, "quantity": quantity}

    def get_cart(self, user_id: str) -> dict[str, Any]:
        """Get the user's cart with product details and total."""
        cart_items = self.redis.get_cart(user_id)
        if not cart_items:
            return {"items": [], "total": 0.0, "item_count": 0}

        items = []
        total = 0.0
        for product_id, quantity in cart_items.items():
            product = self._get_product_info(product_id)
            if product:
                line_total = float(product["price"]) * quantity
                items.append({
                    "product_id": product_id,
                    "name": product["name"],
                    "price": float(product["price"]),
                    "quantity": quantity,
                    "line_total": round(line_total, 2),
                })
                total += line_total

        return {"items": items, "total": round(total, 2), "item_count": len(items)}

    def clear_cart(self, user_id: str) -> dict[str, str]:
        """Clear the user's cart."""
        self.redis.clear_cart(user_id)
        return {"status": "cleared"}

    def checkout(self, user_id: str) -> dict[str, Any]:
        """Convert cart to an order in PostgreSQL."""
        cart = self.get_cart(user_id)
        if not cart["items"]:
            return {"error": "Cart is empty"}

        with db.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO orders (user_id, total_amount, status) VALUES (%s, %s, %s) RETURNING id;",
                (user_id, cart["total"], "completed"),
            )
            result = cursor.fetchone()
            if result is None:
                return {"error": "Failed to create order"}
            order_id = result["id"]

            for item in cart["items"]:
                cursor.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s);",
                    (order_id, item["product_id"], item["quantity"], item["price"]),
                )

        self.redis.clear_cart(user_id)
        logger.info("Checkout complete for %s, order #%d", user_id, order_id)
        return {"status": "order_placed", "order_id": order_id, "total": cart["total"]}

    def _get_product_info(self, product_id: str) -> dict[str, Any] | None:
        """Get product info, using Redis cache when available."""
        cached = self.redis.get_cached_product(product_id)
        if cached:
            return cached

        with db.get_cursor() as cursor:
            cursor.execute("SELECT id, name, price, stock FROM products WHERE id = %s", (product_id,))
            row = cursor.fetchone()
            if row:
                product = dict(row)
                self.redis.cache_product(product_id, product)
                return product
        return None
