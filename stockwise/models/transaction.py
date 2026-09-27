"""Transaction hierarchy: abstract base + concrete Sale/Restock."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from ..constants import TAX_RATE


@dataclass
class TransactionItem:
    sku: str
    name: str
    quantity: int
    unit_price: float

    @property
    def subtotal(self) -> float:
        return round(self.quantity * self.unit_price, 2)


class Transaction(ABC):
    """Abstract base for anything that moves stock and money."""

    def __init__(
        self,
        items: list[TransactionItem],
        timestamp: datetime | None = None,
        tx_id: int | None = None,
    ):
        if not items:
            raise ValueError("A transaction needs at least one item.")
        self.id = tx_id
        self.items = items
        self.timestamp = timestamp or datetime.now()

    @abstractmethod
    def kind(self) -> str:
        """Short label: 'SALE' or 'RESTOCK'."""

    @abstractmethod
    def total(self) -> float:
        """Money total of the transaction."""

    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)


class Sale(Transaction):
    """A customer purchase. Computes VAT and change."""

    def __init__(
        self,
        items: list[TransactionItem],
        amount_tendered: float,
        tax_rate: float = TAX_RATE,
        timestamp: datetime | None = None,
        tx_id: int | None = None,
    ):
        super().__init__(items, timestamp, tx_id)
        self.tax_rate = tax_rate
        self.amount_tendered = round(amount_tendered, 2)
        if self.amount_tendered < self.total():
            raise ValueError(
                f"Insufficient payment: tendered {self.amount_tendered:.2f}, "
                f"total {self.total():.2f}."
            )

    def kind(self) -> str:
        return "SALE"

    def subtotal(self) -> float:
        return round(sum(item.subtotal for item in self.items), 2)

    def tax(self) -> float:
        return round(self.subtotal() * self.tax_rate, 2)

    def total(self) -> float:
        return round(self.subtotal() + self.tax(), 2)

    def change(self) -> float:
        return round(self.amount_tendered - self.total(), 2)


class Restock(Transaction):
    """A supplier delivery that adds stock. unit_price = unit cost."""

    def __init__(
        self,
        items: list[TransactionItem],
        supplier: str = "",
        timestamp: datetime | None = None,
        tx_id: int | None = None,
    ):
        super().__init__(items, timestamp, tx_id)
        self.supplier = supplier

    def kind(self) -> str:
        return "RESTOCK"

    def total(self) -> float:
        return round(sum(item.subtotal for item in self.items), 2)
