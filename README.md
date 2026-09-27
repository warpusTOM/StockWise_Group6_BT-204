# StockWise — Offline Inventory & POS System

A fully **offline** inventory management and point-of-sale system written in
**object-oriented Python**, with a modern desktop GUI (CustomTkinter), a
zero-dependency terminal interface, SQLite persistence, and CSV reporting.

## Features

- **Point of Sale** — search products, build a cart, VAT computation, cash
  tendered / change, printable text receipts
- **Inventory** — add / edit / delete products, per-product restock levels,
  perishable products with expiry dates and automatic near-expiry discounts
- **Restocking** — supplier deliveries recorded as transactions
- **Dashboard** — stock value, units on hand, today's revenue, low-stock alerts
- **Reports** — daily summary, transaction history, one-click CSV export
  (sales / inventory / low-stock)
- **100% offline** — everything lives in a local SQLite file (`stockwise.db`)

## OOP design (why this is an OOP project)

| Pillar | Where |
|---|---|
| Encapsulation | `Inventory` hides the product dict; `Database` hides all SQL; `Cart` hides its item map |
| Inheritance | `PerishableProduct(Product)`; `Sale(Transaction)` and `Restock(Transaction)` |
| Polymorphism | `Product.effective_price()` overridden by `PerishableProduct` (near-expiry discount); `Transaction.kind()/total()` differ per subclass |
| Abstraction | `Transaction(ABC)` with abstract `kind()` / `total()` |
| Composition | `Cart` *has* `TransactionItem`s; `StockWiseSystem` *has* an `Inventory`, a `Database`, and a `ReportGenerator` |
| Facade | `StockWiseSystem` is the single entry point used by both the GUI and the CLI |

## Install & run

```bash
pip install -r requirements.txt

python main.py           # GUI
python main.py --cli     # terminal interface (no dependencies at all)
python main.py --demo    # seed sample products on first run
```

> The GUI needs `customtkinter`. Without it the app automatically falls back
> to the terminal interface.

## Tests

```bash
python -m unittest discover -s tests -t . -v
```

## Project structure

```
StockWise/
├── main.py                 # entry point (GUI by default, --cli for terminal)
├── requirements.txt
├── stockwise/
│   ├── constants.py        # currency, tax rate, DB path — tune here
│   ├── database.py         # SQLite layer (encapsulated SQL)
│   ├── reports.py          # ReportGenerator: summaries + CSV export
│   ├── system.py           # StockWiseSystem facade
│   ├── cli.py              # terminal interface
│   ├── models/
│   │   ├── product.py      # Product, PerishableProduct
│   │   ├── transaction.py  # Transaction (ABC), Sale, Restock, TransactionItem
│   │   ├── cart.py         # Cart
│   │   ├── inventory.py    # Inventory
│   │   └── receipt.py      # Receipt
│   └── gui/
│       └── app.py          # CustomTkinter app (4 tabs)
├── tests/
│   └── test_core.py        # unittest suite
└── docs/
    └── PROPOSAL.md         # project proposal document
```

## Configuration

Edit `stockwise/constants.py`:

```python
CURRENCY = "₱"     # currency symbol used on receipts/reports
TAX_RATE = 0.12    # VAT rate; 0.0 disables tax
```

## License

MIT
