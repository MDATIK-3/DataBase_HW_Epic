import logging

from pymongo import MongoClient  
from pymongo.database import Database  

from src.config import MONGO_CONFIG

logger = logging.getLogger(__name__)


class MongoDBClient:
    def __init__(self):
        self.client = MongoClient(MONGO_CONFIG["uri"])
        self.db: Database = self.client[MONGO_CONFIG["database"]]

    def get_collection(self, name: str):
        """Get a MongoDB collection."""
        return self.db[name]

    def create_indexes(self):
        """Create necessary indexes for all collections."""
        self.db["reviews"].create_index("product_id")
        self.db["reviews"].create_index("user_id")
        self.db["reviews"].create_index("rating")
        self.db["reviews"].create_index([("title", "text"), ("content", "text")])

        self.db["product_specs"].create_index("product_id")
        self.db["product_specs"].create_index("category")

        self.db["seller_profiles"].create_index("seller_id")

        self.db["user_preferences"].create_index("user_id")

        logger.info("MongoDB indexes created successfully")

    def close(self):
        self.client.close()


mongo_client = MongoDBClient()
