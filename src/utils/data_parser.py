"""Utilities for parsing CSV data."""

import pandas as pd

from src.config import DATA_DIR


class DataParser:
    @staticmethod
    def parse_products() -> pd.DataFrame:
        """Parse products CSV file."""
        df = pd.read_csv(DATA_DIR / "products.csv")
        df["PRICE"] = df["PRICE"].astype(float)
        df["TAGS"] = df["TAGS"].apply(lambda x: x.split(","))
        return df

    @staticmethod
    def parse_users() -> pd.DataFrame:
        """Parse users CSV file."""
        df = pd.read_csv(DATA_DIR / "users.csv")
        df["INTERESTS"] = df["INTERESTS"].apply(lambda x: x.split(","))
        df["JOIN_DATE"] = pd.to_datetime(df["JOIN_DATE"])
        return df

    @staticmethod
    def parse_categories() -> pd.DataFrame:
        """Parse categories CSV file."""
        return pd.read_csv(DATA_DIR / "categories.csv")

    @staticmethod
    def parse_sellers() -> pd.DataFrame:
        """Parse sellers CSV file."""
        df = pd.read_csv(DATA_DIR / "sellers.csv")
        df["RATING"] = df["RATING"].astype(float)
        df["JOINED"] = pd.to_datetime(df["JOINED"])
        return df


class CachedDataParser(DataParser):
    """Data parser with caching capability."""

    def __init__(self) -> None:
        self._cache: dict[str, pd.DataFrame] = {}

    def get_products_cached(self) -> pd.DataFrame:
        if "products" not in self._cache:
            self._cache["products"] = DataParser.parse_products()
        return self._cache["products"]

    def get_data(self, data_type: str) -> pd.DataFrame:
        """Get data by type using pattern matching."""
        match data_type:
            case "products":
                return self.get_products_cached()
            case "users":
                return self.parse_users()
            case "categories":
                return self.parse_categories()
            case "sellers":
                return self.parse_sellers()
            case _:
                raise ValueError(f"Unknown data type: {data_type}")
