"""StockWiseSystem — facade used by both the CLI and the GUI."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from .constants import DB_PATH
from .database import Database
from .models.cart import Cart
from .models.inventory import Inventory
from .models.product import PerishableProduct, Product
from .models.transaction import Restock, Sale, Transaction, TransactionItem
from .reports import ReportGenerator


class StockWiseSystem:
    """One entry point for catalog management, sales, restocks, and reports."""

    def __init__(self, db_path: str | Path = DB_PATH):
        self.db = Database(db_path)
        self.inventory = Inventory()
        self.db.load_into(self.inventory)
        self.reports = ReportGenerator(self.db, self.inventory)

    # ---- catalog ----------------------------------------------------
    def register_product(
        self,
        sku: str,
        name: str,
        price: float,
        cost: float = 0.0,
        quantity: int = 0,
        category: str = "General",
        restock_level: int = 5,
        expiry_date: date | None = None,
    ) -> Product:
        if expiry_date is not None:
            product: Product = PerishableProduct(
                sku=sku, name=name, price=price, cost=cost, quantity=quantity,
                category=category, restock_level=restock_level, expiry_date=expiry_date,
            )
        else:
            product = Product(
                sku=sku, name=name, price=price, cost=cost, quantity=quantity,
                category=category, restock_level=restock_level,
            )
        self.inventory.add(product)
        self.db.upsert_product(product)
        return product

    def update_product(self, product: Product) -> None:
        self.inventory.update(product)
        self.db.upsert_product(product)

    def remove_product(self, sku: str) -> None:
        self.inventory.remove(sku)
        self.db.delete_product(sku)

    # ---- operations ---------------------------------------------------
    def sell(self, cart: Cart, amount_tendered: float) -> Sale:
        """Validate payment, deduct stock, persist everything."""
        sale = cart.checkout(amount_tendered)
        for item in sale.items:
            product = self.inventory.get(item.sku)
            product.adjust_stock(-item.quantity)
            self.db.upsert_product(product)
        self.db.record_transaction(sale)
        return sale

    def restock(self, sku: str, quantity: int,
                unit_cost: float | None = None, supplier: str = "") -> Restock:
        product = self.inventory.get(sku)
        cost = product.cost if unit_cost is None else unit_cost
        tx = Restock(
            [TransactionItem(sku=sku, name=product.name,
                             quantity=quantity, unit_price=cost)],
            supplier=supplier,
        )
        product.adjust_stock(quantity)
        if unit_cost is not None:
            product.cost = unit_cost
        self.db.upsert_product(product)
        self.db.record_transaction(tx)
        return tx

    # ---- insights -------------------------------------------------------
    def today_summary(self) -> dict:
        return self.reports.daily_summary(date.today())

    def history(self, limit: int = 100) -> list[Transaction]:
        return self.db.transactions(limit)

    def close(self) -> None:
        self.db.close()

    # ---- demo data -------------------------------------------------------
    def seed_demo_data(self) -> None:
        """Load sample products — only on an empty catalog."""
        if self.inventory.all():
            return
        demo = [
            ("SKU-001", "Instant Noodles", 25.0, 18.0, 48, "Food", 10, None),
            ("SKU-002", "Bottled Water 500ml", 20.0, 12.0, 60, "Beverage", 12, None),
            ("SKU-003", "Iced Coffee 230ml", 45.0, 30.0, 24, "Beverage", 6,
             date.today() + timedelta(days=2)),
            ("SKU-004", "Potato Chips 80g", 35.0, 22.0, 30, "Snacks", 8, None),
            ("SKU-005", "Chocolate Bar", 50.0, 32.0, 15, "Snacks", 5, None),
            ("SKU-006", "Fresh Milk 1L", 95.0, 70.0, 4, "Dairy", 5,
             date.today() + timedelta(days=5)),
        ]
        for sku, name, price, cost, qty, cat, lvl, exp in demo:
            self.register_product(sku, name, price, cost, qty, cat, lvl, exp)
