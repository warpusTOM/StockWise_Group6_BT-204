"""Product catalog domain classes (inheritance + polymorphism)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class Product:
    """Base product. Encapsulates pricing and stock rules.

    Subclasses override effective_price() to change selling behaviour
    without touching the rest of the system (polymorphism).
    """

    sku: str
    name: str
    price: float
    cost: float = 0.0
    quantity: int = 0
    category: str = "General"
    restock_level: int = 5

    def __post_init__(self) -> None:
        if not self.sku.strip() or not self.name.strip():
            raise ValueError("SKU and name are required.")
        if self.price < 0 or self.cost < 0:
            raise ValueError("Price and cost cannot be negative.")
        if self.quantity < 0:
            raise ValueError("Quantity cannot be negative.")

    # ---- stock ----------------------------------------------------
    @property
    def is_low_stock(self) -> bool:
        return self.quantity <= self.restock_level

    def adjust_stock(self, delta: int) -> None:
        new_qty = self.quantity + delta
        if new_qty < 0:
            raise ValueError(f"Not enough stock for {self.name} (have {self.quantity}).")
        self.quantity = new_qty

    # ---- pricing --------------------------------------------------
    def effective_price(self) -> float:
        """Selling price; overridden by subclasses."""
        return round(self.price, 2)

    @property
    def margin(self) -> float:
        return round(self.price - self.cost, 2)

    @property
    def stock_value(self) -> float:
        return round(self.cost * self.quantity, 2)

    def __str__(self) -> str:
        return f"[{self.sku}] {self.name} (qty {self.quantity})"


@dataclass
class PerishableProduct(Product):
    """Product with an expiry date; auto-discounts when near expiry."""

    expiry_date: date | None = None
    near_expiry_days: int = 3
    expiry_discount: float = 0.25

    def days_until_expiry(self) -> int | None:
        if self.expiry_date is None:
            return None
        return (self.expiry_date - date.today()).days

    @property
    def is_expired(self) -> bool:
        days = self.days_until_expiry()
        return days is not None and days < 0

    @property
    def is_near_expiry(self) -> bool:
        days = self.days_until_expiry()
        return days is not None and 0 <= days <= self.near_expiry_days

    def effective_price(self) -> float:
        base = super().effective_price()
        if self.is_near_expiry:
            return round(base * (1 - self.expiry_discount), 2)
        return base
