import pandas as pd

from src.utils.purchase_generator import PurchaseGenerator


class TestPurchaseGenerator:
    def setup_method(self):
        self.generator = PurchaseGenerator()

    def test_generate_purchases(self):
        purchases = self.generator.generate_purchases(20)
        assert isinstance(purchases, pd.DataFrame)
        assert len(purchases) == 20

    def test_purchase_columns(self):
        purchases = self.generator.generate_purchases(5)
        expected_columns = ["user_id", "product_id", "product_name", "quantity", "unit_price", "total_price", "purchase_date"]
        for col in expected_columns:
            assert col in purchases.columns

    def test_quantity_range(self):
        purchases = self.generator.generate_purchases(50)
        assert purchases["quantity"].min() >= 1
        assert purchases["quantity"].max() <= 3

    def test_total_price_calculation(self):
        purchases = self.generator.generate_purchases(10)
        for _, row in purchases.iterrows():
            expected = round(row["unit_price"] * row["quantity"], 2)
            assert row["total_price"] == expected

    def test_user_ids_valid(self):
        purchases = self.generator.generate_purchases(10)
        valid_users = set(self.generator.users["ID"].tolist())
        for uid in purchases["user_id"]:
            assert uid in valid_users

    def test_product_ids_valid(self):
        purchases = self.generator.generate_purchases(10)
        valid_products = set(self.generator.products["ID"].tolist())
        for pid in purchases["product_id"]:
            assert pid in valid_products
