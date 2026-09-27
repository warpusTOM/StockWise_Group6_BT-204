"""SQLite persistence — everything stays on local disk, fully offline."""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

from .constants import DB_PATH
from .models.inventory import Inventory
from .models.product import PerishableProduct, Product
from .models.transaction import Restock, Sale, Transaction, TransactionItem

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    sku           TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    category      TEXT NOT NULL DEFAULT 'General',
    price         REAL NOT NULL,
    cost          REAL NOT NULL DEFAULT 0,
    quantity      INTEGER NOT NULL DEFAULT 0,
    restock_level INTEGER NOT NULL DEFAULT 5,
    expiry_date   TEXT
);
CREATE TABLE IF NOT EXISTS transactions (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    type      TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    total     REAL NOT NULL,
    detail    TEXT
);
CREATE TABLE IF NOT EXISTS transaction_items (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER NOT NULL REFERENCES transactions(id),
    sku            TEXT NOT NULL,
    name           TEXT NOT NULL,
    quantity       INTEGER NOT NULL,
    unit_price     REAL NOT NULL
);
"""


class Database:
    """Encapsulates all SQL — the rest of the app never writes queries."""

    def __init__(self, path: str | Path = DB_PATH):
        self.path = Path(path)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    def close(self) -> None:
        self._conn.close()

    # ---------------- products ----------------
    def upsert_product(self, product: Product) -> None:
        expiry = None
        if isinstance(product, PerishableProduct) and product.expiry_date:
            expiry = product.expiry_date.isoformat()
        self._conn.execute(
            """INSERT INTO products (sku, name, category, price, cost, quantity,
                                     restock_level, expiry_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(sku) DO UPDATE SET
                   name=excluded.name, category=excluded.category,
                   price=excluded.price, cost=excluded.cost,
                   quantity=excluded.quantity,
                   restock_level=excluded.restock_level,
                   expiry_date=excluded.expiry_date""",
            (product.sku, product.name, product.category, product.price,
             product.cost, product.quantity, product.restock_level, expiry),
        )
        self._conn.commit()

    def delete_product(self, sku: str) -> None:
        self._conn.execute("DELETE FROM products WHERE sku = ?", (sku,))
        self._conn.commit()

    def load_into(self, inventory: Inventory) -> Inventory:
        rows = self._conn.execute("SELECT * FROM products ORDER BY name").fetchall()
        for row in rows:
            inventory.add(self._row_to_product(row))
        return inventory

    @staticmethod
    def _row_to_product(row: sqlite3.Row) -> Product:
        if row["expiry_date"]:
            return PerishableProduct(
                sku=row["sku"], name=row["name"], price=row["price"],
                cost=row["cost"], quantity=row["quantity"],
                category=row["category"], restock_level=row["restock_level"],
                expiry_date=date.fromisoformat(row["expiry_date"]),
            )
        return Product(
            sku=row["sku"], name=row["name"], price=row["price"],
            cost=row["cost"], quantity=row["quantity"],
            category=row["category"], restock_level=row["restock_level"],
        )

    # ---------------- transactions ----------------
    def record_transaction(self, tx: Transaction) -> int:
        detail: dict = {}
        if isinstance(tx, Sale):
            detail = {"tendered": tx.amount_tendered, "change": tx.change(),
                      "tax_rate": tx.tax_rate}
        elif isinstance(tx, Restock):
            detail = {"supplier": tx.supplier}
        cur = self._conn.execute(
            "INSERT INTO transactions (type, timestamp, total, detail) VALUES (?, ?, ?, ?)",
            (tx.kind(), tx.timestamp.isoformat(), tx.total(), json.dumps(detail)),
        )
        tx.id = cur.lastrowid
        for item in tx.items:
            self._conn.execute(
                """INSERT INTO transaction_items
                   (transaction_id, sku, name, quantity, unit_price)
                   VALUES (?, ?, ?, ?, ?)""",
                (tx.id, item.sku, item.name, item.quantity, item.unit_price),
            )
        self._conn.commit()
        return tx.id

    def transactions(self, limit: int = 100) -> list[Transaction]:
        rows = self._conn.execute(
            "SELECT * FROM transactions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._row_to_transaction(row) for row in rows]

    def sales_between(self, start: date, end: date) -> list[Sale]:
        rows = self._conn.execute(
            """SELECT * FROM transactions
               WHERE type = 'SALE' AND substr(timestamp, 1, 10) BETWEEN ? AND ?
               ORDER BY id""",
            (start.isoformat(), end.isoformat()),
        ).fetchall()
        return [self._row_to_transaction(row) for row in rows]  # type: ignore[misc]

    def sales_on(self, day: date) -> list[Sale]:
        return self.sales_between(day, day)

    def _row_to_transaction(self, row: sqlite3.Row) -> Transaction:
        items = [
            TransactionItem(sku=r["sku"], name=r["name"],
                            quantity=r["quantity"], unit_price=r["unit_price"])
            for r in self._conn.execute(
                "SELECT * FROM transaction_items WHERE transaction_id = ?", (row["id"],)
            ).fetchall()
        ]
        ts = datetime.fromisoformat(row["timestamp"])
        detail = json.loads(row["detail"] or "{}")
        if row["type"] == "SALE":
            return Sale(items, amount_tendered=row["total"],
                        tax_rate=detail.get("tax_rate", 0.0),
                        timestamp=ts, tx_id=row["id"])
        return Restock(items, supplier=detail.get("supplier", ""),
                       timestamp=ts, tx_id=row["id"])
