"""Entry point.

    python main.py            # GUI (falls back to CLI if customtkinter missing)
    python main.py --cli      # terminal interface
    python main.py --demo     # seed sample products on first run
"""
from __future__ import annotations

import argparse

from stockwise.constants import DB_PATH
from stockwise.system import StockWiseSystem


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="stockwise",
        description="StockWise — Offline Inventory & POS System",
    )
    parser.add_argument("--cli", action="store_true",
                        help="run the terminal interface instead of the GUI")
    parser.add_argument("--demo", action="store_true",
                        help="seed demo data (only if the catalog is empty)")
    parser.add_argument("--db", default=DB_PATH, help="path to the SQLite file")
    args = parser.parse_args()

    system = StockWiseSystem(args.db)
    if args.demo:
        system.seed_demo_data()

    if args.cli:
        from stockwise.cli import run_cli
        run_cli(system)
        return

    try:
        from stockwise.gui.app import run_gui
    except ImportError:
        print("customtkinter is not installed — falling back to CLI.")
        print("Install it with:  pip install customtkinter\n")
        from stockwise.cli import run_cli
        run_cli(system)
        return
    run_gui(system)


if __name__ == "__main__":
    main()
