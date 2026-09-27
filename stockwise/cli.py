"""Terminal interface — zero third-party dependencies."""
from __future__ import annotations

from datetime import date

from .constants import CURRENCY
from .models.cart import Cart
from .models.product import PerishableProduct, Product
from .models.receipt import Receipt
from .system import StockWiseSystem


def _money(value: float) -> str:
    return f"{CURRENCY}{value:,.2f}"


def _pause() -> None:
    input("\n[Enter] to continue...")


def _pick(matches: list[Product]) -> Product | None:
    for i, p in enumerate(matches[:9], 1):
        print(f"  {i}) {p.name} [{p.sku}] — {_money(p.effective_price())} "
              f"(stock {p.quantity})")
    try:
        idx = int(input("Pick #: ").strip()) - 1
        return matches[idx]
    except (ValueError, IndexError):
        print("Invalid pick.")
        return None


def run_cli(system: StockWiseSystem) -> None:
    actions = {"1": _pos, "2": _inventory, "3": _reports, "4": _history}
    while True:
        print("\n===== StockWise — Offline Inventory & POS =====")
        print("1) Point of Sale   2) Inventory   3) Reports   "
              "4) Transactions   0) Exit")
        choice = input("> ").strip()
        if choice == "0":
            print("Bye!")
            return
        action = actions.get(choice)
        if action:
            action(system)


# ---------------------------------------------------------------- POS
def _pos(system: StockWiseSystem) -> None:
    cart = Cart()
    while True:
        print("\n-- POS --")
        print("a) Add item   v) View cart   c) Checkout   b) Back")
        choice = input("> ").strip().lower()
        if choice == "b":
            return
        if choice == "a":
            query = input("SKU or part of name: ").strip()
            matches = system.inventory.search(query)
            if not matches:
                print("No match.")
                continue
            product = matches[0] if len(matches) == 1 else _pick(matches)
            if product is None:
                continue
            try:
                qty = int(input(
                    f"Qty for {product.name} (stock {product.quantity}): "
                ).strip() or "1")
                cart.add(product, qty)
                print(f"Added {qty} x {product.name}")
            except ValueError as exc:
                print(f"Error: {exc}")
        elif choice == "v":
            if not cart.items:
                print("(cart empty)")
            for item in cart.items:
                print(f"  {item.quantity} x {item.name} @ "
                      f"{_money(item.unit_price)} = {_money(item.subtotal)}")
            print(f"  Subtotal {_money(cart.subtotal())} + VAT "
                  f"{_money(cart.tax())} = {_money(cart.total())}")
        elif choice == "c":
            if not cart.items:
                print("Cart is empty.")
                continue
            try:
                tendered = float(input(
                    f"Total {_money(cart.total())} — cash tendered: "
                ).strip())
                sale = system.sell(cart, tendered)
                receipt = Receipt(sale)
                print()
                print(receipt.render())
                print(f"(receipt saved to {receipt.save()})")
                return
            except ValueError as exc:
                print(f"Error: {exc}")


# ---------------------------------------------------------------- Inventory
def _inventory(system: StockWiseSystem) -> None:
    while True:
        print("\n-- Inventory --")
        print("l) List   a) Add product   r) Restock   d) Delete   b) Back")
        choice = input("> ").strip().lower()
        if choice == "b":
            return
        if choice == "l":
            print(f"\n{'SKU':<9}{'Name':<24}{'Cat':<10}{'Price':>9}{'Qty':>5}  Flags")
            for p in system.inventory.all():
                flags = []
                if p.is_low_stock:
                    flags.append("LOW")
                if isinstance(p, PerishableProduct) and p.expiry_date:
                    flags.append(f"exp {p.expiry_date.isoformat()}")
                print(f"{p.sku:<9}{p.name[:22]:<24}{p.category[:9]:<10}"
                      f"{p.price:>9.2f}{p.quantity:>5}  {' '.join(flags)}")
            _pause()
        elif choice == "a":
            try:
                sku = input("SKU: ").strip()
                name = input("Name: ").strip()
                category = input("Category [General]: ").strip() or "General"
                price = float(input("Selling price: "))
                cost = float(input("Cost [0]: ").strip() or "0")
                qty = int(input("Opening qty [0]: ").strip() or "0")
                level = int(input("Restock level [5]: ").strip() or "5")
                raw = input("Expiry YYYY-MM-DD (blank = non-perishable): ").strip()
                expiry = date.fromisoformat(raw) if raw else None
                p = system.register_product(sku, name, price, cost, qty,
                                            category, level, expiry)
                print(f"Added {p}")
            except ValueError as exc:
                print(f"Error: {exc}")
            _pause()
        elif choice == "r":
            sku = input("SKU to restock: ").strip()
            try:
                qty = int(input("Qty to add: "))
                raw_cost = input("Unit cost (blank = keep current): ").strip()
                supplier = input("Supplier (optional): ").strip()
                cost = float(raw_cost) if raw_cost else None
                tx = system.restock(sku, qty, cost, supplier)
                print(f"Restocked. New qty: "
                      f"{system.inventory.get(sku).quantity} "
                      f"(tx #{tx.id}, {_money(tx.total())})")
            except (ValueError, KeyError) as exc:
                print(f"Error: {exc}")
            _pause()
        elif choice == "d":
            sku = input("SKU to delete: ").strip()
            confirm = input(f"Really delete {sku}? [y/N]: ").strip().lower()
            if confirm == "y":
                try:
                    system.remove_product(sku)
                    print("Deleted.")
                except KeyError as exc:
                    print(f"Error: {exc}")
            _pause()


# ---------------------------------------------------------------- Reports
def _reports(system: StockWiseSystem) -> None:
    summary = system.today_summary()
    print(f"\nToday ({summary['date']}): {summary['sales_count']} sales, "
          f"revenue {_money(summary['revenue'])}, "
          f"items sold {summary['items_sold']}")
    low = system.inventory.low_stock()
    if low:
        print("Low stock:")
        for p in low:
            print(f"  ! {p.name} [{p.sku}] — {p.quantity} left "
                  f"(level {p.restock_level})")
    else:
        print("No low-stock items.")
    kind = input("\nExport CSV [sales/inventory/low] or blank to skip: ").strip().lower()
    builders = {
        "sales": system.reports.sales_rows,
        "inventory": system.reports.inventory_rows,
        "low": system.reports.low_stock_rows,
    }
    if kind in builders:
        headers, rows = builders[kind]()
        path = system.reports.export_csv(
            headers, rows, f"exports/{kind}-{date.today().isoformat()}.csv"
        )
        print(f"Saved to {path}")
    _pause()


# ---------------------------------------------------------------- History
def _history(system: StockWiseSystem) -> None:
    print(f"\n{'ID':<5}{'Timestamp':<18}{'Type':<9}{'Items':>6}{'Total':>12}")
    for t in system.history(20):
        print(f"#{t.id:<4}{t.timestamp:%Y-%m-%d %H:%M}   {t.kind():<9}"
              f"{t.item_count():>6}{t.total():>12.2f}")
    _pause()
