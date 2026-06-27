"""
ArtisanMarket - Complete Feature Demo
Run this single file to showcase all features for the video presentation.
Usage: .venv/Scripts/python demo.py
"""

import logging
import time

logging.basicConfig(level=logging.WARNING)


def separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_postgres():
    """Demo 1: PostgreSQL - Relational Data"""
    separator("1. PostgreSQL - Relational Data")
    from src.db.postgres_client import db

    with db.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS count FROM categories")
        row = cursor.fetchone()
        print(f"  Categories: {row['count'] if row else 0}")

        cursor.execute("SELECT COUNT(*) AS count FROM sellers")
        row = cursor.fetchone()
        print(f"  Sellers:    {row['count'] if row else 0}")

        cursor.execute("SELECT COUNT(*) AS count FROM users")
        row = cursor.fetchone()
        print(f"  Users:      {row['count'] if row else 0}")

        cursor.execute("SELECT COUNT(*) AS count FROM products")
        row = cursor.fetchone()
        print(f"  Products:   {row['count'] if row else 0}")

        cursor.execute("SELECT COUNT(*) AS count FROM orders")
        row = cursor.fetchone()
        print(f"  Orders:     {row['count'] if row else 0}")

        print("\n  Sample Products:")
        cursor.execute("SELECT id, name, category, price FROM products ORDER BY id LIMIT 5")
        for row in cursor.fetchall():
            print(f"    {row['id']}: {row['name']} ({row['category']}) - ${row['price']}")

        print("\n  Orders with Items (JOIN query):")
        cursor.execute("""
            SELECT o.id AS order_id, u.name AS customer, p.name AS product,
                   oi.quantity, oi.unit_price
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            ORDER BY o.id
            LIMIT 5
        """)
        for row in cursor.fetchall():
            print(f"    Order #{row['order_id']}: {row['customer']} bought "
                  f"{row['quantity']}x {row['product']} @ ${row['unit_price']}")


def demo_mongodb():
    """Demo 2: MongoDB - Document Store"""
    separator("2. MongoDB - Document Store")
    from src.db.mongodb_client import mongo_client

    print("  Collections:", mongo_client.db.list_collection_names())

    print("\n  Product Review (nested document):")
    review = mongo_client.db["reviews"].find_one({"product_id": "P001"}, {"_id": 0})
    if review:
        print(f"    Product: {review['product_id']} | Rating: {review['rating']}/5")
        print(f"    Title: \"{review['title']}\"")
        print(f"    Verified: {review['verified_purchase']} | Helpful: {review['helpful_votes']}")
        print(f"    Images: {len(review.get('images', []))} | Comments: {len(review.get('comments', []))}")
    else:
        print("    (No reviews found - run document_loader first)")

    print("\n  Jewelry Product Specs (flexible schema):")
    spec = mongo_client.db["product_specs"].find_one({"category": "Jewelry"}, {"_id": 0})
    if spec:
        print(f"    Product: {spec['product_id']} | Category: {spec['category']}")
        for key, val in spec["specs"].items():
            print(f"    {key}: {val}")

    print("\n  Kitchen Product Specs (different shape!):")
    spec2 = mongo_client.db["product_specs"].find_one({"category": "Home & Kitchen"}, {"_id": 0})
    if spec2:
        print(f"    Product: {spec2['product_id']} | Category: {spec2['category']}")
        for key, val in spec2["specs"].items():
            print(f"    {key}: {val}")


def demo_redis_cart():
    """Demo 3: Redis - Shopping Cart"""
    separator("3. Redis - Shopping Cart (Hash + TTL)")
    from src.services.cart_service import CartService

    cart = CartService()
    cart.clear_cart("U001")

    print("  Adding items to cart...")
    r1 = cart.add_item("U001", "P001", 2)
    print(f"    + {r1['product']} x{r1['quantity']}")
    r2 = cart.add_item("U001", "P005", 1)
    print(f"    + {r2['product']} x{r2['quantity']}")

    print("\n  Cart contents:")
    contents = cart.get_cart("U001")
    for item in contents["items"]:
        print(f"    {item['name']}: {item['quantity']} x ${item['price']} = ${item['line_total']}")
    print(f"    TOTAL: ${contents['total']} ({contents['item_count']} items)")

    print("\n  Updating quantity (P001 -> 1)...")
    cart.update_quantity("U001", "P001", 1)

    print("\n  Checkout -> creates PostgreSQL order:")
    result = cart.checkout("U001")
    print(f"    Order #{result['order_id']} placed! Total: ${result['total']}")


def demo_redis_cache():
    """Demo 4: Redis - Search Caching"""
    separator("4. Redis - Search Result Caching")
    from src.db.redis_client import redis_client
    from src.services.search_service import SearchService

    redis_client.client.delete("cache:stats")
    service = SearchService()

    print("  First search for 'wooden' (cache MISS)...")
    t1 = time.time()
    results = service.search_products("wooden")
    t1 = time.time() - t1
    print(f"    Found {len(results)} results in {t1:.4f}s")

    print("\n  Same search again (cache HIT)...")
    t2 = time.time()
    results = service.search_products("wooden")
    t2 = time.time() - t2
    print(f"    Found {len(results)} results in {t2:.4f}s")
    if t1 > 0:
        print(f"    Speedup: {t1/max(t2, 0.0001):.1f}x faster!")

    stats = redis_client.get_cache_stats()
    print(f"\n  Cache Stats: {stats['hits']} hits, {stats['misses']} misses, "
          f"hit rate: {stats['hit_rate']*100:.0f}%")


def demo_neo4j_recommendations():
    """Demo 5: Neo4j - Recommendations"""
    separator("5. Neo4j - Graph-Based Recommendations")
    from src.services.recommendation_service import RecommendationService

    rec = RecommendationService()

    print("  'Also Bought' for P001 (Hand-carved Wooden Bowl):")
    for r in rec.also_bought("P001"):
        print(f"    -> {r['name']} (${r['price']}) - {r['buyer_count']} shared buyers")

    print("\n  'Frequently Bought Together' with P001:")
    for r in rec.frequently_bought_together("P001"):
        print(f"    -> {r['name']} ({r['category']}) - {r['co_purchases']} co-purchases")

    print("\n  Personalized Recommendations for U001 (Emma Thompson):")
    for r in rec.personalized("U001"):
        print(f"    -> {r['name']} ({r['category']}) - score: {r['score']}")

    print("\n  Similar Products to P001:")
    for r in rec.similar_products("P001"):
        print(f"    -> {r['name']} ({r['category']}) - {r['shared_buyers']} shared buyers")


def demo_semantic_search():
    """Demo 6: Semantic Search (pgvector)"""
    separator("6. Semantic Search - pgvector + Sentence Transformers")
    from src.services.search_service import SearchService

    service = SearchService()

    print("  Text search: 'wooden'")
    for r in service.search_products("wooden", limit=5):
        print(f"    {r['id']}: {r['name']} - ${r['price']}")

    print("\n  Semantic search: 'gift for someone who likes cooking'")
    print("  (finds related items even without keyword match)")
    for r in service.semantic_search("gift for someone who likes cooking", limit=5):
        print(f"    {r['id']}: {r['name']} - similarity: {r.get('similarity', 'N/A')}")

    print("\n  'Find Similar' to P001 (Hand-carved Wooden Bowl):")
    for r in service.find_similar_products("P001", limit=5):
        print(f"    {r['id']}: {r['name']} - similarity: {r.get('similarity', 'N/A')}")


def demo_rate_limiting():
    """Demo 7: Redis - Rate Limiting"""
    separator("7. Redis - Rate Limiting")
    from src.db.redis_client import redis_client

    redis_client.client.delete("rate_limit:U001:search")

    print("  Simulating API requests for user U001...")
    for i in range(1, 6):
        allowed = redis_client.rate_limit_check("U001", "search")
        remaining = redis_client.get_rate_limit_remaining("U001", "search")
        print(f"    Request #{i}: {'ALLOWED' if allowed else 'DENIED'} - {remaining} remaining")

    print("\n  Rate limit: 100 requests per 60 seconds (configurable in config.py)")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  ArtisanMarket - Polyglot Persistence Demo")
    print("  4 Databases | 7 Features | 1 Marketplace")
    print("="*60)

    demo_postgres()
    demo_mongodb()
    demo_redis_cart()
    demo_redis_cache()
    demo_neo4j_recommendations()
    demo_semantic_search()
    demo_rate_limiting()

    separator("DEMO COMPLETE")
    print("  Databases used:")
    print("    PostgreSQL  - relational data, orders, vector embeddings")
    print("    MongoDB     - reviews, specs, profiles, preferences")
    print("    Redis       - shopping cart, search cache, rate limiting")
    print("    Neo4j       - recommendations (also bought, personalized)")
    print()
