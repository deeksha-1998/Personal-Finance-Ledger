import sqlite3

DB_FILE = "ledger.db"

def initialize_database():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT,
            type TEXT,
            category TEXT,
            amount REAL,
            account TEXT,
            note TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ledger_id INTEGER,
            action TEXT,
            old_amount REAL,
            new_amount REAL,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("Database successfully created!")

if __name__ == "__main__":
    initialize_database()
