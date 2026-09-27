"""Inventory — encapsulates the product collection."""
from __future__ import annotations

from datetime import date

from .product import PerishableProduct, Product


class Inventory:
    def __init__(self) -> None:
        self._products: dict[str, Product] = {}

    # ---- mutation ---------------------------------------------------
    def add(self, product: Product) -> None:
        if product.sku in self._products:
            raise ValueError(f"SKU {product.sku} already exists.")
        self._products[product.sku] = product

    def update(self, product: Product) -> None:
        if product.sku not in self._products:
            raise KeyError(f"Unknown SKU {product.sku}")
        self._products[product.sku] = product

    def remove(self, sku: str) -> None:
        if sku not in self._products:
            raise KeyError(f"Unknown SKU {sku}")
        del self._products[sku]

    # ---- queries ------------------------------------------------------
    def get(self, sku: str) -> Product:
        if sku not in self._products:
            raise KeyError(f"Unknown SKU {sku}")
        return self._products[sku]

    def find(self, sku: str) -> Product | None:
        return self._products.get(sku)

    def all(self) -> list[Product]:
        return sorted(self._products.values(), key=lambda p: p.name.lower())

    def search(self, query: str) -> list[Product]:
        q = query.strip().lower()
        return [p for p in self.all() if q in p.sku.lower() or q in p.name.lower()]

    def low_stock(self) -> list[Product]:
        return [p for p in self.all() if p.is_low_stock]

    def expiring_soon(self, days: int = 3) -> list[PerishableProduct]:
        result = []
        for p in self._products.values():
            if isinstance(p, PerishableProduct):
                remaining = p.days_until_expiry()
                if remaining is not None and remaining <= days:
                    result.append(p)
        return sorted(result, key=lambda p: p.expiry_date or date.max)

    # ---- aggregates -----------------------------------------------------
    @property
    def total_skus(self) -> int:
        return len(self._products)

    @property
    def total_units(self) -> int:
        return sum(p.quantity for p in self._products.values())

    @property
    def total_value(self) -> float:
        return round(sum(p.stock_value for p in self._products.values()), 2)
