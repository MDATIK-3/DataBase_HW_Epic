"""CLI entry point for ArtisanMarket data management."""

import logging

import click

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@click.group()
def main():
    """ArtisanMarket - Polyglot Persistence CLI"""
    pass


@main.command()
def load_postgres():
    """Load data into PostgreSQL."""
    from src.loaders.relational_loader import RelationalLoader

    loader = RelationalLoader()
    loader.load_all()


@main.command()
def load_mongo():
    """Load data into MongoDB."""
    from src.loaders.document_loader import DocumentLoader

    loader = DocumentLoader()
    loader.load_all()


@main.command()
def load_graph():
    """Load data into Neo4j."""
    from src.loaders.graph_loader import GraphLoader

    loader = GraphLoader()
    loader.load_all()


@main.command()
def load_vectors():
    """Generate and load vector embeddings."""
    from src.loaders.vector_loader import VectorLoader

    loader = VectorLoader()
    loader.load_all()


@main.command()
@click.option("--count", default=100, help="Number of purchases to generate")
def generate_purchases(count):
    """Generate purchase history and load into databases."""
    from src.utils.purchase_generator import PurchaseGenerator

    generator = PurchaseGenerator()
    purchases = generator.generate_purchases(count)
    print(f"Generated {len(purchases)} purchases")
    generator.save_purchases(purchases)
    generator.load_to_postgres(purchases)
    generator.load_to_neo4j(purchases)


@main.command()
def load_all():
    """Load all data into all databases."""
    from src.loaders.document_loader import DocumentLoader
    from src.loaders.graph_loader import GraphLoader
    from src.loaders.relational_loader import RelationalLoader
    from src.loaders.vector_loader import VectorLoader
    from src.utils.purchase_generator import PurchaseGenerator

    print("=" * 50)
    print("Phase 1: Loading relational data (PostgreSQL)")
    print("=" * 50)
    RelationalLoader().load_all()

    print("\n" + "=" * 50)
    print("Phase 2: Loading document data (MongoDB)")
    print("=" * 50)
    DocumentLoader().load_all()

    print("\n" + "=" * 50)
    print("Phase 3: Loading graph data (Neo4j)")
    print("=" * 50)
    GraphLoader().load_all()

    print("\n" + "=" * 50)
    print("Phase 4: Loading vector embeddings (pgvector)")
    print("=" * 50)
    VectorLoader().load_all()

    print("\n" + "=" * 50)
    print("Phase 5: Generating purchase history")
    print("=" * 50)
    generator = PurchaseGenerator()
    purchases = generator.generate_purchases(100)
    generator.save_purchases(purchases)
    generator.load_to_postgres(purchases)
    generator.load_to_neo4j(purchases)

    print("\n" + "=" * 50)
    print("All data loaded successfully!")
    print("=" * 50)


@main.command()
@click.argument("query")
@click.option("--category", default=None, help="Filter by category")
@click.option("--min-price", default=None, type=float, help="Minimum price")
@click.option("--max-price", default=None, type=float, help="Maximum price")
def search(query, category, min_price, max_price):
    """Search for products."""
    from src.services.search_service import SearchService

    service = SearchService()
    results = service.search_products(query, category=category, min_price=min_price, max_price=max_price)
    if not results:
        print("No results found.")
        return
    for r in results:
        print(f"  {r['id']}: {r['name']} - ${r['price']} ({r['category']})")


@main.command()
@click.argument("query")
def semantic(query):
    """Semantic search for products."""
    from src.services.search_service import SearchService

    service = SearchService()
    results = service.semantic_search(query)
    if not results:
        print("No results found.")
        return
    for r in results:
        print(f"  {r['id']}: {r['name']} (similarity: {r.get('similarity', 'N/A')})")


@main.command()
@click.argument("product_id")
def recommend(product_id):
    """Get recommendations for a product."""
    from src.services.recommendation_service import RecommendationService

    service = RecommendationService()

    print(f"\n=== Also Bought ({product_id}) ===")
    for r in service.also_bought(product_id):
        print(f"  {r['id']}: {r['name']} (buyers: {r['buyer_count']})")

    print(f"\n=== Frequently Bought Together ({product_id}) ===")
    for r in service.frequently_bought_together(product_id):
        print(f"  {r['id']}: {r['name']} (co-purchases: {r['co_purchases']})")


@main.command()
@click.argument("user_id")
def personalized(user_id):
    """Get personalized recommendations for a user."""
    from src.services.recommendation_service import RecommendationService

    service = RecommendationService()
    results = service.personalized(user_id)
    if not results:
        print("No recommendations available yet.")
        return
    for r in results:
        print(f"  {r['id']}: {r['name']} ({r['category']}) - score: {r['score']}")


if __name__ == "__main__":
    main()
