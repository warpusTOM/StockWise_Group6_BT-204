import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from stockwise.models.cart import Cart
from stockwise.models.product import PerishableProduct, Product
from stockwise.models.transaction import Sale, TransactionItem
from stockwise.system import StockWiseSystem


class TestProduct(unittest.TestCase):
    def test_base_price(self):
        p = Product("A1", "Apple", 10.0, quantity=10)
        self.assertEqual(p.effective_price(), 10.0)
        self.assertFalse(p.is_low_stock)

    def test_low_stock(self):
        p = Product("A1", "Apple", 10.0, quantity=3, restock_level=5)
        self.assertTrue(p.is_low_stock)

    def test_perishable_discount(self):
        near = PerishableProduct("M1", "Milk", 100.0, quantity=5,
                                 expiry_date=date.today() + timedelta(days=2))
        self.assertEqual(near.effective_price(), 75.0)
        far = PerishableProduct("M2", "Milk", 100.0, quantity=5,
                                expiry_date=date.today() + timedelta(days=30))
        self.assertEqual(far.effective_price(), 100.0)

    def test_negative_stock_raises(self):
        p = Product("A1", "Apple", 10.0, quantity=1)
        with self.assertRaises(ValueError):
            p.adjust_stock(-5)

    def test_invalid_product_raises(self):
        with self.assertRaises(ValueError):
            Product("", "No SKU", 10.0)
        with self.assertRaises(ValueError):
            Product("A1", "Bad", -5.0)


class TestCartAndSale(unittest.TestCase):
    def setUp(self):
        self.product = Product("A1", "Apple", 10.0, quantity=10)

    def test_cart_math(self):
        cart = Cart()
        cart.add(self.product, 2)
        self.assertEqual(cart.subtotal(), 20.0)
        self.assertEqual(cart.tax(), round(20.0 * 0.12, 2))
        self.assertEqual(cart.total(), 22.4)

    def test_over_stock_raises(self):
        cart = Cart()
        cart.add(self.product, 5)
        with self.assertRaises(ValueError):
            cart.add(self.product, 6)

    def test_set_quantity_removes_at_zero(self):
        cart = Cart()
        cart.add(self.product, 3)
        cart.set_quantity(self.product, 0)
        self.assertEqual(cart.items, [])

    def test_insufficient_payment(self):
        items = [TransactionItem("A1", "Apple", 2, 10.0)]
        with self.assertRaises(ValueError):
            Sale(items, amount_tendered=1.0)

    def test_sale_change(self):
        items = [TransactionItem("A1", "Apple", 1, 100.0)]
        sale = Sale(items, amount_tendered=200.0)
        self.assertEqual(sale.total(), 112.0)
        self.assertEqual(sale.change(), 88.0)


class TestSystem(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "test.db"
        self.system = StockWiseSystem(self.db_path)
        self.system.register_product("A1", "Apple", 10.0, cost=6.0, quantity=10)

    def tearDown(self):
        self.system.close()
        self.tmp.cleanup()

    def test_sell_reduces_stock_and_persists(self):
        cart = Cart()
        cart.add(self.system.inventory.get("A1"), 3)
        sale = self.system.sell(cart, 100.0)
        self.assertEqual(self.system.inventory.get("A1").quantity, 7)
        self.assertIsNotNone(sale.id)
        # survives a full reload
        fresh = StockWiseSystem(self.db_path)
        self.assertEqual(fresh.inventory.get("A1").quantity, 7)
        self.assertEqual(len(fresh.db.transactions()), 1)
        fresh.close()

    def test_restock(self):
        tx = self.system.restock("A1", 5, supplier="Acme")
        self.assertEqual(self.system.inventory.get("A1").quantity, 15)
        self.assertEqual(tx.kind(), "RESTOCK")

    def test_duplicate_sku_raises(self):
        with self.assertRaises(ValueError):
            self.system.register_product("A1", "Duplicate", 1.0)

    def test_seed_demo_data_only_once(self):
        # catalog already has A1 -> seed must skip entirely
        self.system.seed_demo_data()
        self.assertEqual(self.system.inventory.total_skus, 1)

    def test_seed_demo_data_on_empty_catalog(self):
        empty_path = Path(self.tmp.name) / "empty.db"
        fresh = StockWiseSystem(empty_path)
        fresh.seed_demo_data()
        self.assertEqual(fresh.inventory.total_skus, 6)
        fresh.close()


if __name__ == "__main__":
    unittest.main()
