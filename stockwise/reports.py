"""CSV reports and daily summaries."""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from .database import Database
from .models.inventory import Inventory
from .models.product import PerishableProduct


class ReportGenerator:
    def __init__(self, db: Database, inventory: Inventory):
        self.db = db
        self.inventory = inventory

    # ---- summaries ---------------------------------------------------
    def daily_summary(self, day: date | None = None) -> dict:
        day = day or date.today()
        sales = self.db.sales_on(day)
        return {
            "date": day.isoformat(),
            "sales_count": len(sales),
            "revenue": round(sum(s.total() for s in sales), 2),
            "items_sold": sum(s.item_count() for s in sales),
            "low_stock_count": len(self.inventory.low_stock()),
        }

    # ---- row builders --------------------------------------------------
    def sales_rows(self) -> tuple[list, list]:
        headers = ["ID", "Timestamp", "Items", "Total"]
        rows = [
            [t.id, f"{t.timestamp:%Y-%m-%d %H:%M:%S}", t.item_count(), f"{t.total():.2f}"]
            for t in self.db.transactions(limit=1000)
            if t.kind() == "SALE"
        ]
        return headers, rows

    def inventory_rows(self) -> tuple[list, list]:
        headers = ["SKU", "Name", "Category", "Price", "Cost", "Qty",
                   "Restock Lvl", "Expiry", "Stock Value", "Low?"]
        rows = []
        for p in self.inventory.all():
            expiry = ""
            if isinstance(p, PerishableProduct) and p.expiry_date:
                expiry = p.expiry_date.isoformat()
            rows.append([p.sku, p.name, p.category, f"{p.price:.2f}", f"{p.cost:.2f}",
                         p.quantity, p.restock_level, expiry, f"{p.stock_value:.2f}",
                         "YES" if p.is_low_stock else ""])
        return headers, rows

    def low_stock_rows(self) -> tuple[list, list]:
        headers, rows = self.inventory_rows()
        flag = headers.index("Low?")
        return headers, [r for r in rows if r[flag] == "YES"]

    # ---- export ----------------------------------------------------------
    @staticmethod
    def export_csv(headers: list, rows: list, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(headers)
            writer.writerows(rows)
        return path
