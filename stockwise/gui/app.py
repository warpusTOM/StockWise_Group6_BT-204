"""CustomTkinter desktop UI — dashboard, POS, inventory, reports."""
from __future__ import annotations

from datetime import date
from tkinter import filedialog, messagebox, simpledialog, ttk

import customtkinter as ctk

from ..constants import APP_NAME, CURRENCY
from ..models.cart import Cart
from ..models.product import PerishableProduct
from ..models.receipt import Receipt
from ..system import StockWiseSystem


def money(value: float) -> str:
    return f"{CURRENCY}{value:,.2f}"


def run_gui(system: StockWiseSystem) -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = StockWiseApp(system)
    app.mainloop()


class StockWiseApp(ctk.CTk):
    def __init__(self, system: StockWiseSystem):
        super().__init__()
        self.system = system
        self.cart = Cart()

        self.title(f"{APP_NAME} — Offline Inventory & POS")
        self.geometry("1150x700")
        self._style_tree()

        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_dash = tabs.add("Dashboard")
        self.tab_pos = tabs.add("Point of Sale")
        self.tab_inv = tabs.add("Inventory")
        self.tab_rep = tabs.add("Reports")

        self._build_dashboard()
        self._build_pos()
        self._build_inventory()
        self._build_reports()
        self.refresh_all()

    # ---------------------------------------------------------------- style
    def _style_tree(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white",
                        fieldbackground="#2b2b2b", rowheight=26, borderwidth=0)
        style.configure("Treeview.Heading", background="#1f6aa5",
                        foreground="white", relief="flat")
        style.map("Treeview", background=[("selected", "#1f6aa5")])

    # ---------------------------------------------------------------- dashboard
    def _build_dashboard(self) -> None:
        cards = ctk.CTkFrame(self.tab_dash)
        cards.pack(fill="x", padx=10, pady=10)
        self.dash_values = {}
        for key, label in [
            ("products", "Products"), ("units", "Units in stock"),
            ("value", "Stock value"), ("revenue", "Today's revenue"),
            ("sales", "Today's sales"), ("low", "Low stock"),
        ]:
            card = ctk.CTkFrame(cards)
            card.pack(side="left", expand=True, fill="both", padx=6, pady=6)
            ctk.CTkLabel(card, text=label, font=("", 13)).pack(pady=(10, 0))
            value = ctk.CTkLabel(card, text="-", font=("", 22, "bold"))
            value.pack(pady=(0, 10))
            self.dash_values[key] = value

        ctk.CTkLabel(self.tab_dash, text="Low stock alerts",
                     font=("", 15, "bold")).pack(anchor="w", padx=14)
        self.low_box = ctk.CTkTextbox(self.tab_dash, height=220, state="disabled")
        self.low_box.pack(fill="both", expand=True, padx=10, pady=(4, 10))

    def refresh_dashboard(self) -> None:
        inv = self.system.inventory
        summary = self.system.today_summary()
        self.dash_values["products"].configure(text=str(inv.total_skus))
        self.dash_values["units"].configure(text=str(inv.total_units))
        self.dash_values["value"].configure(text=money(inv.total_value))
        self.dash_values["revenue"].configure(text=money(summary["revenue"]))
        self.dash_values["sales"].configure(text=str(summary["sales_count"]))
        self.dash_values["low"].configure(text=str(summary["low_stock_count"]))

        self.low_box.configure(state="normal")
        self.low_box.delete("1.0", "end")
        low = inv.low_stock()
        if not low:
            self.low_box.insert("end", "All good — nothing below restock level.\n")
        for p in low:
            extra = ""
            if isinstance(p, PerishableProduct) and p.expiry_date:
                extra = f" | expires {p.expiry_date.isoformat()}"
            self.low_box.insert(
                "end",
                f"! {p.name} [{p.sku}] — {p.quantity} left "
                f"(level {p.restock_level}){extra}\n",
            )
        self.low_box.configure(state="disabled")

    # ---------------------------------------------------------------- POS
    def _build_pos(self) -> None:
        body = ctk.CTkFrame(self.tab_pos)
        body.pack(fill="both", expand=True, padx=6, pady=6)

        left = ctk.CTkFrame(body, width=430)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.search_var = ctk.StringVar()
        entry = ctk.CTkEntry(left, placeholder_text="Search products...",
                             textvariable=self.search_var)
        entry.pack(fill="x", padx=8, pady=8)
        entry.bind("<KeyRelease>", lambda _e: self.refresh_product_picker())
        self.picker = ctk.CTkScrollableFrame(left)
        self.picker.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        right = ctk.CTkFrame(body, width=520)
        right.pack(side="left", fill="both", expand=True)

        cols = ("name", "qty", "price", "subtotal")
        self.cart_tree = ttk.Treeview(right, columns=cols, show="headings", height=12)
        for col, text, w, anchor in [
            ("name", "Item", 200, "w"), ("qty", "Qty", 50, "center"),
            ("price", "Price", 90, "center"), ("subtotal", "Subtotal", 100, "center"),
        ]:
            self.cart_tree.heading(col, text=text)
            self.cart_tree.column(col, width=w, anchor=anchor)
        self.cart_tree.pack(fill="both", expand=True, padx=8, pady=8)

        btn_row = ctk.CTkFrame(right, fg_color="transparent")
        btn_row.pack(fill="x", padx=8)
        ctk.CTkButton(btn_row, text="+1", width=60,
                      command=lambda: self._bump(1)).pack(side="left", padx=3)
        ctk.CTkButton(btn_row, text="-1", width=60,
                      command=lambda: self._bump(-1)).pack(side="left", padx=3)
        ctk.CTkButton(btn_row, text="Remove", width=80, fg_color="#a33",
                      command=self._remove_selected).pack(side="left", padx=3)
        ctk.CTkButton(btn_row, text="Clear", width=80, fg_color="#666",
                      command=self._clear_cart).pack(side="left", padx=3)

        totals = ctk.CTkFrame(right, fg_color="transparent")
        totals.pack(fill="x", padx=8, pady=(6, 0))
        self.total_label = ctk.CTkLabel(totals, text="Total: " + money(0),
                                        font=("", 18, "bold"))
        self.total_label.pack(side="left")

        pay_row = ctk.CTkFrame(right, fg_color="transparent")
        pay_row.pack(fill="x", padx=8, pady=8)
        self.tendered_entry = ctk.CTkEntry(pay_row, placeholder_text="Cash tendered",
                                           width=140)
        self.tendered_entry.pack(side="left", padx=(0, 8))
        ctk.CTkButton(pay_row, text="CHECKOUT", fg_color="#1a7f37", height=36,
                      command=self._checkout).pack(side="left")

    def refresh_product_picker(self) -> None:
        for child in self.picker.winfo_children():
            child.destroy()
        for product in self.system.inventory.search(self.search_var.get()):
            price = product.effective_price()
            label = f"{product.name}  [{product.sku}]\n{money(price)}  |  stock {product.quantity}"
            btn = ctk.CTkButton(
                self.picker, text=label, anchor="w", height=44,
                fg_color="#2b2b2b" if product.quantity else "#442222",
                command=lambda p=product: self._add_to_cart(p),
            )
            btn.pack(fill="x", pady=2)
            if product.quantity <= 0:
                btn.configure(state="disabled")

    def _add_to_cart(self, product) -> None:
        try:
            self.cart.add(product, 1)
        except ValueError as exc:
            messagebox.showerror(APP_NAME, str(exc))
        self.refresh_cart()

    def _selected_sku(self) -> str | None:
        sel = self.cart_tree.selection()
        return sel[0] if sel else None

    def _bump(self, delta: int) -> None:
        sku = self._selected_sku()
        if not sku:
            return
        try:
            product = self.system.inventory.get(sku)
            self.cart.set_quantity(product, self.cart.quantity_of(sku) + delta)
        except (ValueError, KeyError) as exc:
            messagebox.showerror(APP_NAME, str(exc))
        self.refresh_cart()

    def _remove_selected(self) -> None:
        sku = self._selected_sku()
        if sku:
            self.cart.remove(sku)
            self.refresh_cart()

    def _clear_cart(self) -> None:
        self.cart.clear()
        self.refresh_cart()

    def refresh_cart(self) -> None:
        self.cart_tree.delete(*self.cart_tree.get_children())
        for item in self.cart.items:
            self.cart_tree.insert("", "end", iid=item.sku, values=(
                item.name, item.quantity, money(item.unit_price), money(item.subtotal)
            ))
        self.total_label.configure(text=f"Total: {money(self.cart.total())}")

    def _checkout(self) -> None:
        if not self.cart.items:
            messagebox.showinfo(APP_NAME, "Cart is empty.")
            return
        try:
            tendered = float(self.tendered_entry.get())
        except ValueError:
            messagebox.showerror(APP_NAME, "Enter a valid cash amount.")
            return
        try:
            sale = self.system.sell(self.cart, tendered)
        except ValueError as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        receipt = Receipt(sale)
        path = receipt.save()
        self._show_receipt(receipt.render(), path)
        self.cart.clear()
        self.tendered_entry.delete(0, "end")
        self.refresh_all()

    def _show_receipt(self, text: str, path) -> None:
        win = ctk.CTkToplevel(self)
        win.title("Receipt")
        win.geometry("430x540")
        box = ctk.CTkTextbox(win, font=("Consolas", 13))
        box.pack(fill="both", expand=True, padx=10, pady=10)
        box.insert("1.0", text)
        box.configure(state="disabled")
        ctk.CTkLabel(win, text=f"Saved to {path}").pack(pady=(0, 10))
        win.transient(self)

    # ---------------------------------------------------------------- inventory
    def _build_inventory(self) -> None:
        body = ctk.CTkFrame(self.tab_inv)
        body.pack(fill="both", expand=True, padx=6, pady=6)

        cols = ("sku", "name", "category", "price", "cost", "qty", "restock", "expiry")
        self.inv_tree = ttk.Treeview(body, columns=cols, show="headings", height=13)
        for col, text, w, anchor in [
            ("sku", "SKU", 90, "w"), ("name", "Name", 190, "w"),
            ("category", "Category", 100, "w"), ("price", "Price", 80, "center"),
            ("cost", "Cost", 80, "center"), ("qty", "Qty", 60, "center"),
            ("restock", "Restock@", 70, "center"), ("expiry", "Expiry", 100, "center"),
        ]:
            self.inv_tree.heading(col, text=text)
            self.inv_tree.column(col, width=w, anchor=anchor)
        self.inv_tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.inv_tree.tag_configure("low", background="#5a2a2a")
        self.inv_tree.bind("<<TreeviewSelect>>", self._fill_form)

        form = ctk.CTkFrame(body)
        form.pack(fill="x", padx=8, pady=(0, 8))
        self.fields = {}
        specs = [
            ("sku", "SKU"), ("name", "Name"), ("category", "Category"),
            ("price", "Price"), ("cost", "Cost"), ("quantity", "Qty"),
            ("restock_level", "Restock lvl"), ("expiry", "Expiry YYYY-MM-DD"),
        ]
        for i, (key, label) in enumerate(specs):
            ctk.CTkLabel(form, text=label).grid(
                row=(i // 4) * 2, column=i % 4, padx=6, pady=(6, 0), sticky="w")
            entry = ctk.CTkEntry(form, width=200)
            entry.grid(row=(i // 4) * 2 + 1, column=i % 4, padx=6, pady=(0, 6))
            self.fields[key] = entry

        btns = ctk.CTkFrame(body, fg_color="transparent")
        btns.pack(fill="x", padx=8, pady=(0, 8))
        ctk.CTkButton(btns, text="Add / Save",
                      command=self._save_product).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="Restock",
                      command=self._restock_selected).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="Delete", fg_color="#a33",
                      command=self._delete_selected).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="Clear form", fg_color="#666",
                      command=self._clear_form).pack(side="left", padx=4)

    def refresh_inventory(self) -> None:
        self.inv_tree.delete(*self.inv_tree.get_children())
        for p in self.system.inventory.all():
            expiry = ""
            if isinstance(p, PerishableProduct) and p.expiry_date:
                expiry = p.expiry_date.isoformat()
            self.inv_tree.insert(
                "", "end", iid=p.sku,
                values=(p.sku, p.name, p.category, f"{p.price:.2f}",
                        f"{p.cost:.2f}", p.quantity, p.restock_level, expiry),
                tags=("low",) if p.is_low_stock else (),
            )

    def _fill_form(self, _event=None) -> None:
        sku = self._selected_sku_inv()
        if not sku:
            return
        try:
            p = self.system.inventory.get(sku)
        except KeyError:
            return
        values = {
            "sku": p.sku, "name": p.name, "category": p.category,
            "price": str(p.price), "cost": str(p.cost), "quantity": str(p.quantity),
            "restock_level": str(p.restock_level),
            "expiry": (p.expiry_date.isoformat()
                       if isinstance(p, PerishableProduct) and p.expiry_date else ""),
        }
        for key, entry in self.fields.items():
            entry.delete(0, "end")
            entry.insert(0, values[key])

    def _selected_sku_inv(self) -> str | None:
        sel = self.inv_tree.selection()
        return sel[0] if sel else None

    def _clear_form(self) -> None:
        for entry in self.fields.values():
            entry.delete(0, "end")

    def _save_product(self) -> None:
        try:
            sku = self.fields["sku"].get().strip()
            name = self.fields["name"].get().strip()
            category = self.fields["category"].get().strip() or "General"
            price = float(self.fields["price"].get())
            cost = float(self.fields["cost"].get() or 0)
            quantity = int(self.fields["quantity"].get() or 0)
            restock_level = int(self.fields["restock_level"].get() or 5)
            raw_exp = self.fields["expiry"].get().strip()
            expiry = date.fromisoformat(raw_exp) if raw_exp else None
        except ValueError as exc:
            messagebox.showerror(APP_NAME, f"Invalid input: {exc}")
            return

        try:
            existing = self.system.inventory.find(sku)
            if existing is None:
                self.system.register_product(sku, name, price, cost, quantity,
                                             category, restock_level, expiry)
            else:
                if expiry is not None and not isinstance(existing, PerishableProduct):
                    # convert to perishable: re-register under the same SKU
                    self.system.remove_product(sku)
                    self.system.register_product(sku, name, price, cost, quantity,
                                                 category, restock_level, expiry)
                else:
                    existing.name = name
                    existing.category = category
                    existing.price = price
                    existing.cost = cost
                    existing.quantity = quantity
                    existing.restock_level = restock_level
                    if isinstance(existing, PerishableProduct):
                        existing.expiry_date = expiry
                    self.system.update_product(existing)
        except (ValueError, KeyError) as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        self.refresh_all()

    def _restock_selected(self) -> None:
        sku = self._selected_sku_inv()
        if not sku:
            messagebox.showinfo(APP_NAME, "Select a product row first.")
            return
        product = self.system.inventory.get(sku)
        qty = simpledialog.askinteger(
            "Restock", f"Add how many units to {product.name}?", minvalue=1)
        if not qty:
            return
        supplier = simpledialog.askstring("Restock", "Supplier (optional):") or ""
        try:
            self.system.restock(sku, qty, supplier=supplier)
        except (ValueError, KeyError) as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        self.refresh_all()

    def _delete_selected(self) -> None:
        sku = self._selected_sku_inv()
        if not sku:
            return
        if messagebox.askyesno(APP_NAME, f"Delete {sku} permanently?"):
            try:
                self.system.remove_product(sku)
            except KeyError as exc:
                messagebox.showerror(APP_NAME, str(exc))
                return
            self._clear_form()
            self.refresh_all()

    # ---------------------------------------------------------------- reports
    def _build_reports(self) -> None:
        frame = ctk.CTkFrame(self.tab_rep)
        frame.pack(fill="x", padx=10, pady=10)
        self.rep_label = ctk.CTkLabel(frame, text="", justify="left",
                                      font=("", 14))
        self.rep_label.pack(anchor="w", padx=10, pady=10)

        btns = ctk.CTkFrame(self.tab_rep, fg_color="transparent")
        btns.pack(fill="x", padx=10)
        for label, kind in [
            ("Export sales CSV", "sales"),
            ("Export inventory CSV", "inventory"),
            ("Export low-stock CSV", "low"),
        ]:
            ctk.CTkButton(btns, text=label,
                          command=lambda k=kind: self._export(k)).pack(side="left",
                                                                       padx=4)

        ctk.CTkLabel(self.tab_rep, text="Recent transactions",
                     font=("", 15, "bold")).pack(anchor="w", padx=14, pady=(14, 0))
        self.hist_box = ctk.CTkTextbox(self.tab_rep, height=220, state="disabled")
        self.hist_box.pack(fill="both", expand=True, padx=10, pady=(4, 10))

    def refresh_reports(self) -> None:
        s = self.system.today_summary()
        self.rep_label.configure(
            text=f"Today ({s['date']}):  {s['sales_count']} sales  |  "
                 f"revenue {money(s['revenue'])}  |  items sold {s['items_sold']}  |  "
                 f"low-stock items {s['low_stock_count']}"
        )
        self.hist_box.configure(state="normal")
        self.hist_box.delete("1.0", "end")
        for t in self.system.history(30):
            self.hist_box.insert(
                "end",
                f"#{t.id:<4} {t.timestamp:%Y-%m-%d %H:%M}  {t.kind():<8} "
                f"items {t.item_count():<3} {money(t.total())}\n",
            )
        self.hist_box.configure(state="disabled")

    def _export(self, kind: str) -> None:
        builders = {
            "sales": self.system.reports.sales_rows,
            "inventory": self.system.reports.inventory_rows,
            "low": self.system.reports.low_stock_rows,
        }
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"{kind}-{date.today().isoformat()}.csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return
        headers, rows = builders[kind]()
        self.system.reports.export_csv(headers, rows, path)
        messagebox.showinfo(APP_NAME, f"Exported to {path}")

    # ---------------------------------------------------------------- refresh
    def refresh_all(self) -> None:
        self.refresh_dashboard()
        self.refresh_product_picker()
        self.refresh_cart()
        self.refresh_inventory()
        self.refresh_reports()
