"""Text receipt rendering + saving."""
from __future__ import annotations

from pathlib import Path

from ..constants import APP_NAME, CURRENCY
from .transaction import Sale


class Receipt:
    WIDTH = 42

    def __init__(self, sale: Sale):
        self.sale = sale

    def render(self) -> str:
        w = self.WIDTH
        sale = self.sale
        lines = [
            APP_NAME.center(w),
            "OFFICIAL RECEIPT".center(w),
            "=" * w,
            f"Date : {sale.timestamp:%Y-%m-%d %H:%M:%S}",
            f"Sale : #{sale.id if sale.id is not None else '-'}",
            "-" * w,
        ]
        for item in sale.items:
            lines.append(f"{item.name[:24]:<24} x{item.quantity}")
            left = f"  @ {CURRENCY}{item.unit_price:,.2f}"
            right = f"{CURRENCY}{item.subtotal:,.2f}"
            lines.append(left + right.rjust(w - len(left)))
        lines += [
            "-" * w,
            self._row("Subtotal", f"{CURRENCY}{sale.subtotal():,.2f}"),
            self._row(f"VAT ({sale.tax_rate:.0%})", f"{CURRENCY}{sale.tax():,.2f}"),
            self._row("TOTAL", f"{CURRENCY}{sale.total():,.2f}"),
            self._row("Cash", f"{CURRENCY}{sale.amount_tendered:,.2f}"),
            self._row("Change", f"{CURRENCY}{sale.change():,.2f}"),
            "=" * w,
            "Thank you!".center(w),
        ]
        return "\n".join(lines)

    def save(self, directory: str | Path = "receipts") -> Path:
        folder = Path(directory)
        folder.mkdir(parents=True, exist_ok=True)
        stamp = self.sale.timestamp.strftime("%Y%m%d-%H%M%S")
        path = folder / f"receipt-{self.sale.id or stamp}.txt"
        path.write_text(self.render(), encoding="utf-8")
        return path

    @staticmethod
    def _row(label: str, value: str) -> str:
        return label + value.rjust(Receipt.WIDTH - len(label))
