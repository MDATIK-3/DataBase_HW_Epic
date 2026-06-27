"""Load data into MongoDB document store."""

import logging
import random
from datetime import datetime, timedelta

from src.db.mongodb_client import mongo_client
from src.utils.data_parser import DataParser

logger = logging.getLogger(__name__)

random.seed(42)

REVIEW_TITLES = [
    "Amazing quality!",
    "Love this product",
    "Exceeded expectations",
    "Beautiful craftsmanship",
    "Great value for money",
    "Unique and well-made",
    "Perfect gift",
    "Absolutely stunning",
    "Highly recommend",
    "Good but could be better",
    "Decent quality",
    "Not what I expected",
    "Wonderful addition to my home",
    "Exactly as described",
    "Fast shipping, great item",
]

REVIEW_CONTENTS = [
    "The craftsmanship on this piece is incredible. You can tell it was made with care and attention to detail.",
    "I bought this as a gift and the recipient absolutely loved it. The quality is outstanding.",
    "Beautiful product that looks even better in person than in the photos. Very happy with my purchase.",
    "This is exactly what I was looking for. The materials are high quality and it arrived well-packaged.",
    "A truly unique handmade item. I appreciate the artisan's skill and creativity.",
    "Good quality overall, though the color was slightly different from what I expected.",
    "Perfect for my home decor. It adds a wonderful handmade touch to the room.",
    "I've purchased several items from this seller and they never disappoint.",
    "The attention to detail is remarkable. This is a one-of-a-kind piece.",
    "Solid construction and beautiful design. Worth every penny.",
]

COMMENT_TEXTS = [
    "I agree, this is fantastic!",
    "Thanks for the detailed review!",
    "I had a similar experience.",
    "This helped me decide to purchase.",
    "Great review, very helpful!",
]

SPEC_TEMPLATES = {
    "Home & Kitchen": {
        "materials": ["acacia wood", "bamboo", "ceramic", "stoneware", "cast iron", "copper"],
        "care": ["Hand wash only", "Dishwasher safe", "Oil regularly", "Wipe with damp cloth"],
        "dimensions_range": {"length": (6, 18), "width": (6, 18), "height": (2, 12)},
    },
    "Fashion": {
        "materials": ["merino wool", "alpaca wool", "silk", "linen", "leather", "cotton"],
        "sizes": ["XS", "S", "M", "L", "XL"],
        "care": ["Hand wash cold", "Dry flat", "Dry clean only", "Machine wash gentle"],
    },
    "Jewelry": {
        "materials": ["sterling silver", "copper", "brass", "gold-filled", "glass beads", "gemstone"],
        "closure_types": ["lobster clasp", "toggle clasp", "elastic", "hook", "magnetic"],
        "length_options": ["16 inches", "18 inches", "20 inches", "24 inches", "adjustable"],
    },
    "Home Decor": {
        "materials": ["cotton rope", "reclaimed wood", "ceramic", "glass", "steel", "wool"],
        "mounting": ["wall mount", "freestanding", "hanging", "tabletop"],
        "dimensions_range": {"length": (8, 48), "width": (8, 36), "height": (2, 24)},
    },
    "Stationery": {
        "materials": ["leather", "recycled paper", "brass", "resin", "cedar wood"],
        "page_count_range": (100, 300),
        "features": ["ribbon bookmark", "elastic closure", "lay-flat binding", "acid-free paper"],
    },
    "Beauty": {
        "ingredients": ["lavender oil", "coconut oil", "shea butter", "activated charcoal", "beeswax", "tea tree oil"],
        "skin_types": ["all skin types", "sensitive", "oily", "dry", "combination"],
        "volume_options": ["2 oz", "4 oz", "8 oz"],
    },
}


class DocumentLoader:
    def __init__(self):
        self.parser = DataParser()

    def load_reviews(self):
        """Generate and load product reviews into MongoDB."""
        collection = mongo_client.get_collection("reviews")
        collection.drop()

        products = self.parser.parse_products()
        users = self.parser.parse_users()
        user_ids = users["ID"].tolist()

        reviews = []
        for _, product in products.iterrows():
            num_reviews = random.randint(1, 4)
            reviewers = random.sample(user_ids, min(num_reviews, len(user_ids)))

            for user_id in reviewers:
                review_date = datetime.now() - timedelta(days=random.randint(1, 365))
                comments = []
                if random.random() > 0.6:
                    num_comments = random.randint(1, 3)
                    for _ in range(num_comments):
                        commenter = random.choice(user_ids)
                        comments.append(
                            {
                                "user_id": commenter,
                                "content": random.choice(COMMENT_TEXTS),
                                "created_at": review_date + timedelta(days=random.randint(1, 30)),
                            }
                        )

                review = {
                    "product_id": product["ID"],
                    "user_id": user_id,
                    "rating": random.randint(3, 5),
                    "title": random.choice(REVIEW_TITLES),
                    "content": random.choice(REVIEW_CONTENTS),
                    "images": [f"https://images.artisanmarket.com/reviews/{product['ID']}_{i}.jpg" for i in range(random.randint(0, 2))],
                    "helpful_votes": random.randint(0, 30),
                    "verified_purchase": random.random() > 0.3,
                    "created_at": review_date,
                    "comments": comments,
                }
                reviews.append(review)

        collection.insert_many(reviews)
        collection.create_index("product_id")
        collection.create_index("user_id")
        collection.create_index("rating")
        logger.info("Loaded %d reviews", len(reviews))
        print(f"Loaded {len(reviews)} reviews into MongoDB")

    def load_product_specs(self):
        """Generate and load product specifications into MongoDB."""
        collection = mongo_client.get_collection("product_specs")
        collection.drop()

        products = self.parser.parse_products()
        specs_docs = []

        for _, product in products.iterrows():
            category = str(product["CATEGORY"])
            template = SPEC_TEMPLATES.get(category, {})
            specs = {}

            if "materials" in template:
                specs["material"] = random.choice(template["materials"])

            if "care" in template:
                specs["care_instructions"] = random.sample(template["care"], min(2, len(template["care"])))

            if "dimensions_range" in template:
                dims = template["dimensions_range"]
                specs["dimensions"] = {
                    "length": random.randint(*dims["length"]),
                    "width": random.randint(*dims["width"]),
                    "height": random.randint(*dims["height"]),
                    "unit": "inches",
                }

            if "sizes" in template:
                specs["available_sizes"] = template["sizes"]

            if "closure_types" in template:
                specs["closure"] = random.choice(template["closure_types"])

            if "length_options" in template:
                specs["chain_length"] = random.choice(template["length_options"])

            if "mounting" in template:
                specs["display_type"] = random.choice(template["mounting"])

            if "ingredients" in template:
                specs["key_ingredients"] = random.sample(template["ingredients"], min(3, len(template["ingredients"])))

            if "skin_types" in template:
                specs["suitable_for"] = random.choice(template["skin_types"])

            if "volume_options" in template:
                specs["size"] = random.choice(template["volume_options"])

            if "features" in template:
                specs["features"] = random.sample(template["features"], min(2, len(template["features"])))

            if "page_count_range" in template:
                specs["page_count"] = random.randint(*template["page_count_range"])

            specs["weight_grams"] = random.randint(50, 2000)
            specs["handmade"] = True
            specs["eco_friendly"] = random.random() > 0.4

            doc = {
                "product_id": product["ID"],
                "category": category,
                "specs": specs,
            }
            specs_docs.append(doc)

        collection.insert_many(specs_docs)
        collection.create_index("product_id")
        collection.create_index("category")
        logger.info("Loaded %d product specs", len(specs_docs))
        print(f"Loaded {len(specs_docs)} product specs into MongoDB")

    def load_seller_profiles(self):
        """Generate and load rich seller profiles into MongoDB."""
        collection = mongo_client.get_collection("seller_profiles")
        collection.drop()

        sellers = self.parser.parse_sellers()
        products = self.parser.parse_products()
        profiles = []

        for _, seller in sellers.iterrows():
            seller_products = products[products["SELLER_ID"] == seller["ID"]]
            portfolio = []
            for _, p in seller_products.iterrows():
                portfolio.append(
                    {
                        "product_id": p["ID"],
                        "name": p["NAME"],
                        "image": f"https://images.artisanmarket.com/products/{p['ID']}.jpg",
                        "featured": random.random() > 0.5,
                    }
                )

            profile = {
                "seller_id": seller["ID"],
                "name": seller["NAME"],
                "bio": f"{seller['NAME']} specializes in {str(seller['SPECIALTY']).lower()}. Each piece is handcrafted with attention to detail and passion for quality.",
                "specialty": str(seller["SPECIALTY"]),
                "rating": float(seller["RATING"]),
                "joined": seller["JOINED"],
                "location": random.choice(["Portland, OR", "Brooklyn, NY", "Austin, TX", "Asheville, NC", "Santa Fe, NM", "Sedona, AZ"]),
                "social_links": {
                    "instagram": f"@{str(seller['NAME']).lower().replace(' ', '')}",
                    "website": f"https://www.{str(seller['NAME']).lower().replace(' ', '')}.com",
                },
                "portfolio": portfolio,
                "response_time": f"{random.randint(1, 24)} hours",
                "total_sales": random.randint(50, 500),
                "accepts_custom_orders": random.random() > 0.3,
            }
            profiles.append(profile)

        collection.insert_many(profiles)
        collection.create_index("seller_id")
        logger.info("Loaded %d seller profiles", len(profiles))
        print(f"Loaded {len(profiles)} seller profiles into MongoDB")

    def load_user_preferences(self):
        """Generate and load user preference/behavior data into MongoDB."""
        collection = mongo_client.get_collection("user_preferences")
        collection.drop()

        users = self.parser.parse_users()
        products = self.parser.parse_products()
        product_ids = products["ID"].tolist()
        categories = products["CATEGORY"].unique().tolist()

        prefs = []
        for _, user in users.iterrows():
            viewed = random.sample(product_ids, min(random.randint(5, 15), len(product_ids)))
            fav_categories = random.sample(categories, min(random.randint(1, 3), len(categories)))

            pref = {
                "user_id": user["ID"],
                "favorite_categories": fav_categories,
                "recently_viewed": viewed[:10],
                "wishlist": random.sample(product_ids, min(random.randint(0, 5), len(product_ids))),
                "price_range_preference": {
                    "min": random.choice([0, 10, 20, 30]),
                    "max": random.choice([50, 100, 150, 200]),
                },
                "preferred_materials": random.sample(
                    ["wood", "ceramic", "leather", "silver", "wool", "cotton", "glass", "bamboo"],
                    random.randint(1, 3),
                ),
                "notification_preferences": {
                    "email_deals": random.random() > 0.4,
                    "new_arrivals": random.random() > 0.5,
                    "price_drops": random.random() > 0.3,
                },
                "search_history": random.sample(
                    ["wooden bowl", "ceramic mug", "leather journal", "candle", "necklace", "scarf", "basket", "vase", "soap", "pillow"],
                    random.randint(2, 5),
                ),
            }
            prefs.append(pref)

        collection.insert_many(prefs)
        collection.create_index("user_id")
        logger.info("Loaded %d user preferences", len(prefs))
        print(f"Loaded {len(prefs)} user preferences into MongoDB")

    def load_all(self):
        """Load all document data into MongoDB."""
        print("Loading reviews...")
        self.load_reviews()

        print("Loading product specifications...")
        self.load_product_specs()

        print("Loading seller profiles...")
        self.load_seller_profiles()

        print("Loading user preferences...")
        self.load_user_preferences()

        mongo_client.create_indexes()
        print("Document data loading complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loader = DocumentLoader()
    loader.load_all()
