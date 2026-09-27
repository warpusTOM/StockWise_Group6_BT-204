# Project Proposal

## Title

**StockWise: An Offline Inventory Management and Point-of-Sale System
Built with Object-Oriented Python**

**Proponent:** warpusTOM
**Course:** Object-Oriented Programming (Python)
**Date:** September 27, 2026

---

## 1. Introduction

Small stores, school canteens, and student organizations still track stock
and sales on paper or in spreadsheets. These methods are error-prone: stock
counts drift, sales records get lost, and there is no quick way to know
which items are running low. Commercial POS systems solve this but usually
require a subscription **and a constant internet connection**, which is not
always available.

**StockWise** is a fully offline inventory management and point-of-sale
(POS) system. All data is stored locally in an SQLite database; the system
works with zero internet connectivity. The project is designed as a
practical application of object-oriented programming principles.

## 2. Statement of the Problem

- Manual stock tracking leads to inaccurate counts and unexpected stockouts.
- Sales records on paper cannot be summarized quickly for daily reports.
- Perishable goods expire unnoticed, causing losses.
- Existing POS software requires internet access and recurring fees.

## 3. Objectives

### General
To design and implement an offline inventory and POS system that
demonstrates the four pillars of OOP in Python.

### Specific
1. Record and manage products, including perishable items with expiry dates.
2. Process sales with cart management, tax computation, change calculation,
   and printed receipts.
3. Track restocking deliveries per supplier.
4. Alert the user when a product falls below its restock level.
5. Generate daily sales summaries and export reports to CSV.
6. Persist all data locally using SQLite.

## 4. Scope and Limitations

**In scope:** single-user desktop operation; product, sale, and restock
management; receipt printing to text files; CSV export; low-stock and
expiry tracking.

**Out of scope:** multi-user / network operation, barcode hardware,
online payment integration, cloud synchronization.

## 5. Methodology — OOP Design

| OOP concept | Implementation |
|---|---|
| Encapsulation | `Inventory`, `Database`, and `Cart` hide their internal data structures |
| Inheritance | `PerishableProduct` extends `Product`; `Sale` and `Restock` extend `Transaction` |
| Polymorphism | `effective_price()` behaves differently for perishables; `kind()`/`total()` differ per transaction type |
| Abstraction | `Transaction` is an abstract base class with abstract methods |
| Composition | `Cart` is composed of `TransactionItem`s; `StockWiseSystem` composes `Inventory`, `Database`, and `ReportGenerator` |
| Facade pattern | `StockWiseSystem` exposes one clean API consumed by both the GUI and the CLI |

**Development approach:** iterative — domain model first, then persistence,
then the terminal interface, then the GUI, with unit tests throughout.

## 6. Technology Stack

- **Language:** Python 3.11+
- **Database:** SQLite (standard library `sqlite3`)
- **GUI:** CustomTkinter / Tkinter
- **Testing:** `unittest`
- **Version control:** Git / GitHub

## 7. Expected Output

A working desktop application (`python main.py`) with:

1. Dashboard — stock totals, today's revenue, low-stock alerts
2. Point of Sale — product search, cart, checkout, receipt
3. Inventory — product CRUD, restocking
4. Reports — daily summary, transaction history, CSV export

Plus this proposal, a README, and a passing unit-test suite.
