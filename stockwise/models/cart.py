"""Shopping cart — composition: a Cart *has* TransactionItems."""
from __future__ import annotations

from ..constants import TAX_RATE
from .product import Product
from .transaction import Sale, TransactionItem


class Cart:
    def __init__(self) -> None:
        self._items: dict[str, TransactionItem] = {}

    # ---- mutation -------------------------------------------------
    def add(self, product: Product, quantity: int = 1) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        self.set_quantity(product, self.quantity_of(product.sku) + quantity)

    def set_quantity(self, product: Product, quantity: int) -> None:
        if quantity <= 0:
            self.remove(product.sku)
            return
        if quantity > product.quantity:
            raise ValueError(f"Only {product.quantity} of {product.name} in stock.")
        self._items[product.sku] = TransactionItem(
            sku=product.sku,
            name=product.name,
            quantity=quantity,
            unit_price=product.effective_price(),
        )

    def remove(self, sku: str) -> None:
        self._items.pop(sku, None)

    def clear(self) -> None:
        self._items.clear()

    # ---- queries --------------------------------------------------
    @property
    def items(self) -> list[TransactionItem]:
        return list(self._items.values())

    def quantity_of(self, sku: str) -> int:
        item = self._items.get(sku)
        return item.quantity if item else 0

    def subtotal(self) -> float:
        return round(sum(item.subtotal for item in self.items), 2)

    def tax(self, rate: float = TAX_RATE) -> float:
        return round(self.subtotal() * rate, 2)

    def total(self, rate: float = TAX_RATE) -> float:
        return round(self.subtotal() + self.tax(rate), 2)

    # ---- checkout ---------------------------------------------------
    def checkout(self, amount_tendered: float, tax_rate: float = TAX_RATE) -> Sale:
        """Build a Sale (validates payment). Does NOT clear the cart."""
        return Sale(self.items, amount_tendered, tax_rate)
