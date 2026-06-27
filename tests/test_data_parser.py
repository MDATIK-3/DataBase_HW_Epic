"""Tests for data parser utilities."""

import pandas as pd
import pytest

from src.utils.data_parser import CachedDataParser, DataParser


class TestDataParser:
    def setup_method(self):
        self.parser = DataParser()

    def test_parse_products(self):
        df = self.parser.parse_products()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 60
        assert "ID" in df.columns
        assert "NAME" in df.columns
        assert "PRICE" in df.columns
        assert "TAGS" in df.columns
        assert df["PRICE"].dtype == float
        assert isinstance(df.iloc[0]["TAGS"], list)

    def test_parse_users(self):
        df = self.parser.parse_users()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 30
        assert "ID" in df.columns
        assert "EMAIL" in df.columns
        assert isinstance(df.iloc[0]["INTERESTS"], list)
        assert pd.api.types.is_datetime64_any_dtype(df["JOIN_DATE"])

    def test_parse_categories(self):
        df = self.parser.parse_categories()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 6
        assert "ID" in df.columns
        assert "NAME" in df.columns

    def test_parse_sellers(self):
        df = self.parser.parse_sellers()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 45
        assert "ID" in df.columns
        assert "RATING" in df.columns
        assert df["RATING"].dtype == float


class TestCachedDataParser:
    def test_caching(self):
        parser = CachedDataParser()
        df1 = parser.get_products_cached()
        df2 = parser.get_products_cached()
        assert df1 is df2

    def test_get_data(self):
        parser = CachedDataParser()
        df = parser.get_data("products")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_get_data_invalid(self):
        parser = CachedDataParser()
        with pytest.raises(ValueError):
            parser.get_data("invalid_type")
