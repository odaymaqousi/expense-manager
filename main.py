import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3


# =========================
# Database
# =========================

conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    amount REAL NOT NULL,
    type TEXT NOT NULL,
    category TEXT NOT NULL
)
""")

conn.commit()


# =========================
# Main Functions
# =========================

def update_summary():
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='Income'")
    income = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='Expense'")
    expenses = cursor.fetchone()[0] or 0

    balance = income - expenses

    income_label.config(text=f"{income:.2f}")
    expense_label.config(text=f"{expenses:.2f}")
    balance_label.config(text=f"{balance:.2f}")


def refresh_table():
    for item in table.get_children():
        table.delete(item)

    search = search_var.get().lower()
    selected_type = filter_var.get()

    cursor.execute("SELECT * FROM transactions ORDER BY id DESC")
    rows = cursor.fetchall()

    for row in rows:
        transaction_id, description, amount, transaction_type, category = row

        if search and search not in description.lower() and search not in category.lower():
            continue

        if selected_type != "All" and transaction_type != selected_type:
            continue

        table.insert(
            "",
            "end",
            values=(
                description,
                f"{amount:.2f}",
                transaction_type,
                category
            ),
            iid=str(transaction_id)
        )

    update_summary()


def clear_filters():
    search_var.set("")
    filter_var.set("All")
    refresh_table()


# =========================
# Add Transaction
# =========================

def add_transaction():
    window = tk.Toplevel(root)
    window.title("Add Transaction")
    window.geometry("400x350")
    window.resizable(False, False)

    ttk.Label(window, text="Description").pack(pady=(20, 5))
    description_entry = ttk.Entry(window, width=35)
    description_entry.pack()

    ttk.Label(window, text="Amount").pack(pady=(15, 5))
    amount_entry = ttk.Entry(window, width=35)
    amount_entry.pack()

    ttk.Label(window, text="Type").pack(pady=(15, 5))
    type_var = tk.StringVar(value="Expense")
    type_combo = ttk.Combobox(
        window,
        textvariable=type_var,
        values=["Income", "Expense"],
        state="readonly",
        width=32
    )
    type_combo.pack()

    ttk.Label(window, text="Category").pack(pady=(15, 5))
    category_entry = ttk.Entry(window, width=35)
    category_entry.pack()

    def save_transaction():
        description = description_entry.get().strip()
        amount_text = amount_entry.get().strip()
        transaction_type = type_var.get()
        category = category_entry.get().strip()

        if not description or not amount_text or not category:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Enter a valid positive amount.")
            return

        cursor.execute("""
            INSERT INTO transactions
            (description, amount, type, category)
            VALUES (?, ?, ?, ?)
        """, (description, amount, transaction_type, category))

        conn.commit()

        refresh_table()
        window.destroy()

    ttk.Button(
        window,
        text="Save Transaction",
        command=save_transaction
    ).pack(pady=25)


# =========================
# Delete Transaction
# =========================

def delete_transaction():
    selected = table.selection()

    if not selected:
        messagebox.showwarning(
            "No Selection",
            "Please select a transaction first."
        )
        return

    transaction_id = selected[0]

    confirm = messagebox.askyesno(
        "Confirm Delete",
        "Are you sure you want to delete this transaction?"
    )

    if confirm:
        cursor.execute(
            "DELETE FROM transactions WHERE id=?",
            (transaction_id,)
        )

        conn.commit()
        refresh_table()


# =========================
# Edit Transaction
# =========================

def edit_transaction():
    selected = table.selection()

    if not selected:
        messagebox.showwarning(
            "No Selection",
            "Please select a transaction first."
        )
        return

    transaction_id = selected[0]

    cursor.execute(
        "SELECT * FROM transactions WHERE id=?",
        (transaction_id,)
    )

    transaction = cursor.fetchone()

    if not transaction:
        return

    _, description, amount, transaction_type, category = transaction

    window = tk.Toplevel(root)
    window.title("Edit Transaction")
    window.geometry("400x350")
    window.resizable(False, False)

    ttk.Label(window, text="Description").pack(pady=(20, 5))
    description_entry = ttk.Entry(window, width=35)
    description_entry.insert(0, description)
    description_entry.pack()

    ttk.Label(window, text="Amount").pack(pady=(15, 5))
    amount_entry = ttk.Entry(window, width=35)
    amount_entry.insert(0, str(amount))
    amount_entry.pack()

    ttk.Label(window, text="Type").pack(pady=(15, 5))

    type_var = tk.StringVar(value=transaction_type)

    type_combo = ttk.Combobox(
        window,
        textvariable=type_var,
        values=["Income", "Expense"],
        state="readonly",
        width=32
    )

    type_combo.pack()

    ttk.Label(window, text="Category").pack(pady=(15, 5))
    category_entry = ttk.Entry(window, width=35)
    category_entry.insert(0, category)
    category_entry.pack()

    def save_changes():
        new_description = description_entry.get().strip()
        amount_text = amount_entry.get().strip()
        new_type = type_var.get()
        new_category = category_entry.get().strip()

        if not new_description or not amount_text or not new_category:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        try:
            new_amount = float(amount_text)

            if new_amount <= 0:
                raise ValueError

        except ValueError:
            messagebox.showerror(
                "Error",
                "Enter a valid positive amount."
            )
            return

        cursor.execute("""
            UPDATE transactions
            SET description=?, amount=?, type=?, category=?
            WHERE id=?
        """, (
            new_description,
            new_amount,
            new_type,
            new_category,
            transaction_id
        ))

        conn.commit()

        refresh_table()
        window.destroy()

    ttk.Button(
        window,
        text="Save Changes",
        command=save_changes
    ).pack(pady=25)


# =========================
# Statistics
# =========================

def show_statistics():
    cursor.execute("SELECT COUNT(*) FROM transactions")
    total_transactions = cursor.fetchone()[0]

    cursor.execute(
        "SELECT SUM(amount) FROM transactions WHERE type='Income'"
    )
    total_income = cursor.fetchone()[0] or 0

    cursor.execute(
        "SELECT SUM(amount) FROM transactions WHERE type='Expense'"
    )
    total_expenses = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT MAX(amount)
        FROM transactions
        WHERE type='Expense'
    """)
    biggest_expense = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE type='Expense'
        GROUP BY category
        ORDER BY total DESC
        LIMIT 1
    """)

    most_expensive_category = cursor.fetchone()

    if most_expensive_category:
        category_name = most_expensive_category[0]
        category_amount = most_expensive_category[1]
    else:
        category_name = "None"
        category_amount = 0

    balance = total_income - total_expenses

    window = tk.Toplevel(root)
    window.title("Statistics")
    window.geometry("450x450")
    window.resizable(False, False)

    ttk.Label(
        window,
        text="Expense Manager Statistics",
        font=("Arial", 18, "bold")
    ).pack(pady=20)

    stats_frame = ttk.Frame(window)
    stats_frame.pack(fill="both", expand=True, padx=30)

    stats = [
        ("Total Transactions", str(total_transactions)),
        ("Total Income", f"{total_income:.2f}"),
        ("Total Expenses", f"{total_expenses:.2f}"),
        ("Balance", f"{balance:.2f}"),
        ("Biggest Expense", f"{biggest_expense:.2f}"),
        (
            "Top Expense Category",
            f"{category_name} ({category_amount:.2f})"
        )
    ]

    for name, value in stats:
        row = ttk.Frame(stats_frame)
        row.pack(fill="x", pady=8)

        ttk.Label(
            row,
            text=name,
            font=("Arial", 11, "bold")
        ).pack(side="left")

        ttk.Label(
            row,
            text=value
        ).pack(side="right")

    ttk.Button(
        window,
        text="Close",
        command=window.destroy
    ).pack(pady=20)


# =========================
# Close Program
# =========================

def close_program():
    conn.close()
    root.destroy()


# =========================
# Main Window
# =========================

root = tk.Tk()
root.title("Expense Manager")
root.geometry("900x650")
root.minsize(800, 600)


# Title

ttk.Label(
    root,
    text="Expense Manager",
    font=("Arial", 24, "bold")
).pack(pady=20)


# Summary

summary_frame = ttk.Frame(root)
summary_frame.pack(fill="x", padx=30)

income_card = ttk.LabelFrame(
    summary_frame,
    text="Total Income"
)
income_card.pack(
    side="left",
    expand=True,
    fill="both",
    padx=5
)

income_label = ttk.Label(
    income_card,
    text="0.00",
    font=("Arial", 18, "bold")
)
income_label.pack(pady=15)


expense_card = ttk.LabelFrame(
    summary_frame,
    text="Total Expenses"
)
expense_card.pack(
    side="left",
    expand=True,
    fill="both",
    padx=5
)

expense_label = ttk.Label(
    expense_card,
    text="0.00",
    font=("Arial", 18, "bold")
)
expense_label.pack(pady=15)


balance_card = ttk.LabelFrame(
    summary_frame,
    text="Balance"
)
balance_card.pack(
    side="left",
    expand=True,
    fill="both",
    padx=5
)

balance_label = ttk.Label(
    balance_card,
    text="0.00",
    font=("Arial", 18, "bold")
)
balance_label.pack(pady=15)


# Search and Filter

filter_frame = ttk.Frame(root)
filter_frame.pack(fill="x", padx=30, pady=20)

search_var = tk.StringVar()

search_entry = ttk.Entry(
    filter_frame,
    textvariable=search_var,
    width=35
)
search_entry.pack(side="left", padx=5)

search_entry.insert(0, "")

filter_var = tk.StringVar(value="All")

filter_combo = ttk.Combobox(
    filter_frame,
    textvariable=filter_var,
    values=["All", "Income", "Expense"],
    state="readonly",
    width=15
)
filter_combo.pack(side="left", padx=5)

ttk.Button(
    filter_frame,
    text="Clear",
    command=clear_filters
).pack(side="left", padx=5)


# Buttons

button_frame = ttk.Frame(root)
button_frame.pack(fill="x", padx=30, pady=5)

ttk.Button(
    button_frame,
    text="Add Transaction",
    command=add_transaction
).pack(side="left", padx=5)

ttk.Button(
    button_frame,
    text="Edit Selected",
    command=edit_transaction
).pack(side="left", padx=5)

ttk.Button(
    button_frame,
    text="Delete Selected",
    command=delete_transaction
).pack(side="left", padx=5)

ttk.Button(
    button_frame,
    text="Statistics",
    command=show_statistics
).pack(side="right", padx=5)


# Transaction Table

table_frame = ttk.Frame(root)
table_frame.pack(
    fill="both",
    expand=True,
    padx=30,
    pady=15
)

columns = (
    "Description",
    "Amount",
    "Type",
    "Category"
)

table = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings"
)

table.heading("Description", text="Description")
table.heading("Amount", text="Amount")
table.heading("Type", text="Type")
table.heading("Category", text="Category")

table.column("Description", width=250)
table.column("Amount", width=120)
table.column("Type", width=120)
table.column("Category", width=180)

scrollbar = ttk.Scrollbar(
    table_frame,
    orient="vertical",
    command=table.yview
)

table.configure(yscrollcommand=scrollbar.set)

table.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")


# Search / Filter Events

search_var.trace_add(
    "write",
    lambda *args: refresh_table()
)

filter_combo.bind(
    "<<ComboboxSelected>>",
    lambda event: refresh_table()
)


# Start

refresh_table()

root.protocol(
    "WM_DELETE_WINDOW",
    close_program
)

root.mainloop()