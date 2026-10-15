import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from PIL import Image, ImageTk
from database import initialize_database

DB_FILE = "ledger.db"

# ============================================================
#                DATABASE FUNCTIONS (LEDGER)
# ============================================================
def insert_row(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO ledger(datetime, type, category, amount, account, note)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data["datetime"], data["type"], data["category"],
        data["amount"], data["account"], data["note"]
    ))
    conn.commit()
    conn.close()

def update_amount(row_id, new_amt):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE ledger SET amount=? WHERE id=?", (new_amt, row_id))
    conn.commit()
    conn.close()

def delete_row(row_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM ledger WHERE id=?", (row_id,))
    conn.commit()
    conn.close()

def fetch_all_with_audit():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT 
            l.id, l.datetime, l.type, l.category,
            l.amount, l.account, l.note,
            (SELECT GROUP_CONCAT(action || '@' || timestamp, ' | ')
             FROM audit_log WHERE ledger_id = l.id)
        FROM ledger l
        ORDER BY l.id DESC;
    """)
    rows = c.fetchall()
    conn.close()
    return rows

# ============================================================
#                USER LOGIN DATABASE
# ============================================================
def ensure_user_table():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()

    # Default user if no users exist
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users(username, password) VALUES (?, ?)", ("admin", "1234"))
        conn.commit()

    conn.close()

def validate_login(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None

# ============================================================
#                CRUD WRAPPERS FOR GUI
# ============================================================
def add_data():
    try:
        amt = float(amount_entry.get())
    except:
        messagebox.showerror("Error", "Amount must be numeric.")
        return

    data = {
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": type_var.get(),
        "category": category_entry.get(),
        "amount": amt,
        "account": account_entry.get(),
        "note": note_entry.get()
    }

    insert_row(data)
    load_table()
    clear_inputs()

def update_data():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Select", "Select a row first.")
        return

    row_id = selected[0]
    try:
        new_amt = float(amount_entry.get())
    except:
        messagebox.showerror("Invalid", "Amount must be numeric.")
        return

    update_amount(row_id, new_amt)
    load_table()

def delete_data():
    selected = tree.selection()
    if not selected:
        return
    row_id = selected[0]
    delete_row(row_id)
    load_table()

def load_table():
    tree.delete(*tree.get_children())
    for row in fetch_all_with_audit():
        tree.insert("", "end", iid=row[0], values=row)

def clear_inputs():
    category_entry.delete(0, tk.END)
    amount_entry.delete(0, tk.END)
    account_entry.delete(0, tk.END)
    note_entry.delete(0, tk.END)

# ============================================================
#                MAIN LEDGER WINDOW (AFTER LOGIN)
# ============================================================
def open_ledger_window():
    login_window.destroy()  # Close login window

    global root
    root = tk.Tk()
    root.title("Personal Finance Ledger")
    root.geometry("1200x700")

    # Soft Theme Colors
    BG_MINT = "#e8f5f2"
    FRAME_WHITE = "#ffffff"
    ACCENT_GREEN = "#2e8b77"
    FONT_LABEL = ("Segoe UI", 11)
    FONT_ENTRY = ("Segoe UI", 11)
    FONT_BUTTON = ("Segoe UI", 10, "bold")

    # ---------------------- Background ----------------------
    canvas = tk.Canvas(root, highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    def resize_bg(event):
        global bg_img_resized
        bg_resized = bg_original.resize((event.width, event.height))
        bg_img_resized = ImageTk.PhotoImage(bg_resized)
        canvas.create_image(0, 0, image=bg_img_resized, anchor="nw")

    try:
        bg_original = Image.open("bg.jpg")
        bg_img_resized = None
        canvas.bind("<Configure>", resize_bg)
    except:
        canvas.configure(bg=BG_MINT)

    # ---------------------- INPUT FRAME ---------------------------
    frame = tk.Frame(canvas, bg=FRAME_WHITE, bd=2, relief="ridge")
    frame.place(relx=0.02, rely=0.03, relwidth=0.44, relheight=0.44)

    def add_label(row, text):
        tk.Label(frame, text=text, bg=FRAME_WHITE, fg="#333",
                 font=FONT_LABEL).grid(row=row, column=0, padx=10, pady=8, sticky="w")

    def add_entry(row):
        e = tk.Entry(frame, font=FONT_ENTRY)
        e.grid(row=row, column=1, padx=10, pady=8, sticky="ew")
        return e

    frame.grid_columnconfigure(1, weight=1)

    add_label(0, "Type:")
    global type_var
    type_var = tk.StringVar(value="expense")
    type_box = ttk.Combobox(
        frame, textvariable=type_var, values=["income", "expense"],
        state="readonly", font=FONT_ENTRY
    )
    type_box.grid(row=0, column=1, padx=10, pady=8, sticky="ew")

    add_label(1, "Category:")
    global category_entry
    category_entry = add_entry(1)

    add_label(2, "Amount:")
    global amount_entry
    amount_entry = add_entry(2)

    add_label(3, "Account:")
    global account_entry
    account_entry = add_entry(3)

    add_label(4, "Note:")
    global note_entry
    note_entry = add_entry(4)

    # ---------------------- BUTTONS -------------------------------
    button_frame = tk.Frame(frame, bg=FRAME_WHITE)
    button_frame.grid(row=5, column=0, columnspan=2, pady=15)

    def make_button(text, color, command):
        return tk.Button(
            button_frame, text=text, command=command,
            bg=color, fg="white", font=FONT_BUTTON,
            relief="flat", padx=15, pady=5
        )

    make_button("Add", ACCENT_GREEN, add_data).grid(row=0, column=0, padx=10)
    make_button("Update", "#3b6ea5", update_data).grid(row=0, column=1, padx=10)
    make_button("Delete", "#b33939", delete_data).grid(row=0, column=2, padx=10)

    # ============================================================
    #                TABLE VIEW (FIXED ORDER!)
    # ============================================================
    global tree

    cols = ("id", "datetime", "type", "category", "amount",
            "account", "note", "audit")

    tree = ttk.Treeview(canvas, columns=cols, show="headings")

    style = ttk.Style()
    style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
    style.configure("Treeview", font=("Segoe UI", 10), rowheight=24)

    for col in cols:
        tree.heading(col, text=col.upper())
        tree.column(col, width=140, anchor="center")

    tree.place(relx=0.02, rely=0.50, relwidth=0.96, relheight=0.47)

    # NOW load data (must be after placing!)
    load_table()

    root.mainloop()

# ============================================================
#                LOGIN WINDOW
# ============================================================
ensure_user_table()

login_window = tk.Tk()
login_window.title("Login")
login_window.geometry("400x300")
login_window.configure(bg="#e8f5f2")

tk.Label(login_window, text="LOGIN", font=("Segoe UI", 16, "bold"),
         bg="#e8f5f2", fg="#2e8b77").pack(pady=20)

tk.Label(login_window, text="Username:", bg="#e8f5f2",
         font=("Segoe UI", 11)).pack()
entry_user = tk.Entry(login_window, font=("Segoe UI", 11))
entry_user.pack(pady=5)

tk.Label(login_window, text="Password:", bg="#e8f5f2",
         font=("Segoe UI", 11)).pack()
entry_pass = tk.Entry(login_window, show="*", font=("Segoe UI", 11))
entry_pass.pack(pady=5)

def attempt_login():
    if validate_login(entry_user.get(), entry_pass.get()):
        open_ledger_window()
    else:
        messagebox.showerror("Error", "Invalid username or password.")

tk.Button(
    login_window, text="Login", command=attempt_login,
    bg="#2e8b77", fg="white", font=("Segoe UI", 11, "bold"),
    relief="flat", padx=20, pady=5
).pack(pady=20)

login_window.mainloop()
