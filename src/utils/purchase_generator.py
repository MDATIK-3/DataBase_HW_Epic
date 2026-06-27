"""Generate random purchase history."""

import logging
import random
from datetime import datetime, timedelta

import pandas as pd

from src.db.neo4j_client import neo4j_client
from src.db.postgres_client import db
from src.utils.data_parser import DataParser

logger = logging.getLogger(__name__)
random.seed(42)

INTEREST_TO_CATEGORY = {
    "sustainable living": "Home & Kitchen",
    "home decor": "Home Decor",
    "cooking": "Home & Kitchen",
    "woodworking": "Home & Kitchen",
    "crafts": "Home & Kitchen",
    "minimalism": "Home Decor",
    "fashion": "Fashion",
    "jewelry": "Jewelry",
    "art": "Home Decor",
    "outdoor": "Home & Kitchen",
    "rustic decor": "Home Decor",
    "leather goods": "Fashion",
    "wellness": "Beauty",
    "natural beauty": "Beauty",
    "yoga": "Beauty",
    "reading": "Stationery",
    "stationery": "Stationery",
    "vintage": "Fashion",
    "bohemian style": "Home Decor",
    "textiles": "Fashion",
    "plants": "Home Decor",
    "entertaining": "Home & Kitchen",
    "ceramics": "Home & Kitchen",
    "eco-friendly": "Home & Kitchen",
    "zero waste": "Home & Kitchen",
    "modern art": "Home Decor",
    "design": "Home Decor",
    "beach lifestyle": "Home Decor",
    "natural materials": "Home & Kitchen",
    "meditation": "Beauty",
    "aromatherapy": "Beauty",
    "scandinavian design": "Home Decor",
    "wool": "Fashion",
    "winter goods": "Fashion",
    "urban gardening": "Home & Kitchen",
    "sustainability": "Home & Kitchen",
    "coastal decor": "Home Decor",
    "nautical": "Home Decor",
    "tea culture": "Home & Kitchen",
    "asian crafts": "Home Decor",
    "calligraphy": "Stationery",
    "cultural crafts": "Home Decor",
    "books": "Stationery",
    "hiking": "Fashion",
    "outdoor gear": "Fashion",
    "zen gardens": "Home Decor",
    "vintage fashion": "Fashion",
    "antiques": "Home Decor",
    "barbecue": "Home & Kitchen",
    "smoking": "Home & Kitchen",
    "artisan foods": "Home & Kitchen",
    "desert plants": "Home Decor",
    "southwestern art": "Home Decor",
    "colonial history": "Stationery",
    "restoration": "Home & Kitchen",
    "urban renewal": "Home Decor",
    "community art": "Home Decor",
    "tech": "Stationery",
    "modern design": "Home Decor",
    "mountain life": "Fashion",
    "wool crafts": "Fashion",
    "outdoor adventures": "Fashion",
    "surfing": "Fashion",
    "beach art": "Home Decor",
    "sustainable": "Home & Kitchen",
    "leather crafts": "Fashion",
    "rustic style": "Home Decor",
    "tools": "Home & Kitchen",
    "handmade": "Home & Kitchen",
    "music": "Home Decor",
    "handmade instruments": "Home Decor",
    "southern charm": "Home Decor",
    "bbq": "Home & Kitchen",
    "outdoor cooking": "Home & Kitchen",
    "wood crafts": "Home & Kitchen",
}


class PurchaseGenerator:
    def __init__(self):
        self.parser = DataParser()
        self.users = self.parser.parse_users()
        self.products = self.parser.parse_products()

    def _get_preferred_products(self, interests: list[str]) -> pd.DataFrame:
        """Get products matching user interests via category mapping."""
        preferred_categories = set()
        for interest in interests:
            cat = INTEREST_TO_CATEGORY.get(interest.strip().lower())
            if cat:
                preferred_categories.add(cat)

        if not preferred_categories:
            return self.products

        matched = self.products[self.products["CATEGORY"].isin(list(preferred_categories))]
        return pd.DataFrame(matched) if len(matched) > 0 else self.products

    def generate_purchases(self, num_purchases: int = 100) -> pd.DataFrame:
        """Generate random purchases based on user interests."""
        purchases = []

        for _ in range(num_purchases):
            user = self.users.sample(1).iloc[0]
            user_join = user["JOIN_DATE"]
            now = datetime.now()

            days_since_join = (now - user_join).days
            if days_since_join <= 0:
                days_since_join = 1

            purchase_date = user_join + timedelta(days=random.randint(1, days_since_join))

            preferred = self._get_preferred_products(user["INTERESTS"])
            product = preferred.sample(1).iloc[0] if random.random() < 0.8 else self.products.sample(1).iloc[0]

            quantity = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]

            purchases.append(
                {
                    "user_id": user["ID"],
                    "product_id": product["ID"],
                    "product_name": product["NAME"],
                    "quantity": quantity,
                    "unit_price": float(product["PRICE"]),
                    "total_price": round(float(product["PRICE"]) * quantity, 2),
                    "purchase_date": purchase_date.strftime("%Y-%m-%d"),
                }
            )

        return pd.DataFrame(purchases)

    def load_to_postgres(self, purchases: pd.DataFrame):
        """Load purchases into PostgreSQL orders and order_items tables."""
        with db.get_cursor() as cursor:
            for _, row in purchases.iterrows():
                cursor.execute(
                    """
                    INSERT INTO orders (user_id, order_date, total_amount, status)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (row["user_id"], row["purchase_date"], row["total_price"], "completed"),
                )
                result = cursor.fetchone()
                if result is None:
                    continue
                order_id = result["id"]

                cursor.execute(
                    """
                    INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (order_id, row["product_id"], row["quantity"], row["unit_price"]),
                )

        logger.info("Loaded %d purchases into PostgreSQL", len(purchases))
        print(f"Loaded {len(purchases)} purchases into PostgreSQL")

    def load_to_neo4j(self, purchases: pd.DataFrame):
        """Load purchases as relationships into Neo4j."""
        for _, row in purchases.iterrows():
            neo4j_client.add_purchase(
                user_id=str(row["user_id"]),
                product_id=str(row["product_id"]),
                quantity=int(row["quantity"]),
                date=str(row["purchase_date"]),
            )

        logger.info("Loaded %d purchase relationships into Neo4j", len(purchases))
        print(f"Loaded {len(purchases)} purchase relationships into Neo4j")

    def save_purchases(self, purchases: pd.DataFrame, filename: str = "purchases.csv"):
        """Save generated purchases to CSV."""
        from src.config import DATA_DIR

        filepath = DATA_DIR / filename
        purchases.to_csv(filepath, index=False)
        logger.info("Saved purchases to %s", filepath)
        print(f"Saved purchases to {filepath}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generator = PurchaseGenerator()

    print("Generating purchases...")
    purchases = generator.generate_purchases(100)

    print(f"Generated {len(purchases)} purchases")

    print("Saving to CSV...")
    generator.save_purchases(purchases)

    print("Loading to PostgreSQL...")
    generator.load_to_postgres(purchases)

    print("Loading to Neo4j...")
    generator.load_to_neo4j(purchases)

    print("Purchase generation complete!")
