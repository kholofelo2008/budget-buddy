"""Budget Buddy - a multi-view personal budgeting app built with Python and Flet.

Views:
  1. Dashboard - balance, income, expenses and spending by category
  2. Add       - a validated form for adding income or an expense
  3. History   - every transaction, with delete
  4. Goals     - monthly budget limit per category with progress bars

Author: Kholofelo Maluleke (FNB App Academy - Intro to Python)
"""

from datetime import date

import flet as ft

PRIMARY = "#0F766E"
ACCENT = "#F59E0B"
INCOME_GREEN = "#16A34A"
EXPENSE_RED = "#DC2626"
CARD_BG = "#FFFFFF"
PAGE_BG = "#F1F5F9"

CATEGORIES = ["Food", "Transport", "Data & Airtime", "Rent", "Books", "Entertainment", "Other"]


class Budget:
    """Holds all transactions and budget limits (in memory)."""

    def __init__(self):
        self.transactions = [
            {"id": 1, "kind": "Income", "category": "Allowance", "amount": 3000.0,
             "note": "Monthly allowance", "date": date.today().isoformat()},
            {"id": 2, "kind": "Expense", "category": "Food", "amount": 450.0,
             "note": "Groceries", "date": date.today().isoformat()},
            {"id": 3, "kind": "Expense", "category": "Transport", "amount": 120.0,
             "note": "Uber to campus", "date": date.today().isoformat()},
        ]
        self.limits = {c: 500.0 for c in CATEGORIES}
        self.next_id = 4

    def add(self, kind, category, amount, note):
        self.transactions.append({
            "id": self.next_id, "kind": kind, "category": category,
            "amount": amount, "note": note, "date": date.today().isoformat(),
        })
        self.next_id += 1

    def delete(self, tx_id):
        self.transactions = [t for t in self.transactions if t["id"] != tx_id]

    def total(self, kind):
        return sum(t["amount"] for t in self.transactions if t["kind"] == kind)

    def balance(self):
        return self.total("Income") - self.total("Expense")

    def spent_in(self, category):
        return sum(t["amount"] for t in self.transactions
                   if t["kind"] == "Expense" and t["category"] == category)


def money(value):
    return f"R{value:,.2f}"


def card(content, padding=16):
    return ft.Container(content=content, bgcolor=CARD_BG, border_radius=14,
                        padding=padding,
                        shadow=ft.BoxShadow(blur_radius=8, color="#22000000"))


def main(page: ft.Page):
    page.title = "Budget Buddy"
    page.bgcolor = PAGE_BG
    page.theme = ft.Theme(color_scheme_seed=PRIMARY)
    page.padding = 0

    budget = Budget()
    body = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=14)

    def notify(message, color=PRIMARY):
        page.show_dialog(ft.SnackBar(content=ft.Text(message), bgcolor=color))

    # ---------- Dashboard ----------
    def dashboard_view():
        stat = lambda label, value, color: card(ft.Column([
            ft.Text(label, size=13, color="#64748B"),
            ft.Text(money(value), size=20, weight=ft.FontWeight.BOLD, color=color),
        ], spacing=4), padding=14)

        rows = []
        expenses = budget.total("Expense") or 1
        for cat in CATEGORIES:
            spent = budget.spent_in(cat)
            if spent:
                rows.append(ft.Column([
                    ft.Row([ft.Text(cat), ft.Text(money(spent), weight=ft.FontWeight.BOLD)],
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.ProgressBar(value=spent / expenses, color=ACCENT, bgcolor="#E2E8F0"),
                ], spacing=4))
        if not rows:
            rows.append(ft.Text("No expenses yet.", color="#64748B"))

        bal = budget.balance()
        return [
            ft.Container(
                content=ft.Column([
                    ft.Text("Current balance", color="#CCFBF1"),
                    ft.Text(money(bal), size=34, weight=ft.FontWeight.BOLD, color="white"),
                ]),
                gradient=ft.LinearGradient(colors=[PRIMARY, "#14B8A6"]),
                border_radius=18, padding=22,
            ),
            ft.Row([
                ft.Container(stat("Income", budget.total("Income"), INCOME_GREEN), expand=True),
                ft.Container(stat("Expenses", budget.total("Expense"), EXPENSE_RED), expand=True),
            ]),
            card(ft.Column([ft.Text("Spending by category", size=16,
                                    weight=ft.FontWeight.BOLD)] + rows, spacing=10)),
        ]

    # ---------- Add transaction (form) ----------
    def add_view():
        kind = ft.SegmentedButton(
            selected=["Expense"],
            segments=[ft.Segment(value="Expense", label=ft.Text("Expense")),
                      ft.Segment(value="Income", label=ft.Text("Income"))],
        )
        category = ft.Dropdown(label="Category", value="Food",
                               options=[ft.DropdownOption(key=c, text=c)
                                        for c in CATEGORIES + ["Allowance", "Salary", "Bursary"]])
        amount = ft.TextField(label="Amount (R)", keyboard_type=ft.KeyboardType.NUMBER,
                              prefix_icon=ft.Icons.PAYMENTS)
        note = ft.TextField(label="Note (optional)", max_length=40)

        def save(e):
            amount.error_text = None
            try:
                value = float(amount.value.replace(",", "."))
                if value <= 0:
                    raise ValueError
            except (ValueError, AttributeError):
                amount.error_text = "Enter a positive number"
                page.update()
                return
            chosen = list(kind.selected)[0]
            budget.add(chosen, category.value, value, note.value or category.value)
            notify(f"{chosen} of {money(value)} saved")
            show(0)

        return [
            ft.Text("Add a transaction", size=22, weight=ft.FontWeight.BOLD),
            card(ft.Column([
                kind, category, amount, note,
                ft.FilledButton("Save transaction", icon=ft.Icons.SAVE, on_click=save,
                                style=ft.ButtonStyle(bgcolor=PRIMARY)),
            ], spacing=14)),
        ]

    # ---------- History ----------
    def history_view():
        def remove(tx_id):
            def handler(e):
                budget.delete(tx_id)
                notify("Transaction deleted", EXPENSE_RED)
                show(2)
            return handler

        items = []
        for t in reversed(budget.transactions):
            is_income = t["kind"] == "Income"
            items.append(card(ft.Row([
                ft.Icon(ft.Icons.ARROW_DOWNWARD if is_income else ft.Icons.ARROW_UPWARD,
                        color=INCOME_GREEN if is_income else EXPENSE_RED),
                ft.Column([
                    ft.Text(t["note"], weight=ft.FontWeight.BOLD),
                    ft.Text(f'{t["category"]} · {t["date"]}', size=12, color="#64748B"),
                ], expand=True, spacing=2),
                ft.Text(("+" if is_income else "-") + money(t["amount"]),
                        color=INCOME_GREEN if is_income else EXPENSE_RED,
                        weight=ft.FontWeight.BOLD),
                ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="Delete",
                              on_click=remove(t["id"])),
            ]), padding=10))
        if not items:
            items.append(ft.Text("No transactions yet.", color="#64748B"))
        return [ft.Text("History", size=22, weight=ft.FontWeight.BOLD)] + items

    # ---------- Goals / budget limits ----------
    def goals_view():
        controls = [ft.Text("Monthly limits", size=22, weight=ft.FontWeight.BOLD)]
        for cat in CATEGORIES:
            spent = budget.spent_in(cat)
            limit = budget.limits[cat]
            ratio = min(spent / limit, 1.0) if limit else 0
            over = spent > limit
            field = ft.TextField(value=str(int(limit)), width=110, dense=True,
                                 prefix="R", keyboard_type=ft.KeyboardType.NUMBER)

            def update_limit(e, c=cat, f=field):
                try:
                    budget.limits[c] = max(float(f.value), 0)
                    notify(f"{c} limit set to {money(budget.limits[c])}")
                    show(3)
                except ValueError:
                    f.error_text = "Number"
                    page.update()

            field.on_submit = update_limit
            controls.append(card(ft.Column([
                ft.Row([ft.Text(cat, weight=ft.FontWeight.BOLD, expand=True), field,
                        ft.IconButton(ft.Icons.CHECK, on_click=update_limit)]),
                ft.ProgressBar(value=ratio, color=EXPENSE_RED if over else INCOME_GREEN,
                               bgcolor="#E2E8F0"),
                ft.Text(f"{money(spent)} of {money(limit)}" + ("  -  over budget!" if over else ""),
                        size=12, color=EXPENSE_RED if over else "#64748B"),
            ], spacing=6), padding=12))
        return controls

    views = [dashboard_view, add_view, history_view, goals_view]

    def show(index):
        nav.selected_index = index
        body.controls = views[index]()
        page.update()

    nav = ft.NavigationBar(
        selected_index=0,
        on_change=lambda e: show(e.control.selected_index),
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD, label="Dashboard"),
            ft.NavigationBarDestination(icon=ft.Icons.ADD_CIRCLE, label="Add"),
            ft.NavigationBarDestination(icon=ft.Icons.HISTORY, label="History"),
            ft.NavigationBarDestination(icon=ft.Icons.FLAG, label="Goals"),
        ],
    )
    page.navigation_bar = nav
    page.appbar = ft.AppBar(title=ft.Text("Budget Buddy", color="white",
                                          weight=ft.FontWeight.BOLD),
                            bgcolor=PRIMARY, center_title=True)
    page.add(ft.Container(body, padding=16, expand=True))
    show(0)


if __name__ == "__main__":
    ft.run(main)
