import sqlite3
from pathlib import Path

def seed_system_envelopes(cursor):
    """Inject the immutable Master Pool and Miscellaneous noeds unto the B-tree."""
    
    cursor.execute('''
        INSERT OR IGNORE INTO Envelopes (envelope_id, name, allocated_amount, current_balance)
        VALUES (1, 'Master Pool', 0.0, 0.0)
    ''')
    
    cursor.execute('''
        INSERT OR IGNORE INTO Envelopes (envelope_id, name, allocated_amount, current_balance)
        VALUES (2, 'Miscellaneous', 0.0, 0.0)
    ''')

def initialize_database():
    
    db_path = Path("apex_finance.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Table 1 : Envelopes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Envelopes (
        envelope_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        allocated_amount REAL DEFAULT 0.0,
        current_balance REAL DEFAULT 0.0
    )
    ''')
    
    # Table 2 : Transactions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        envelope_id INTEGER,
        amount REAL NOT NULL,
        transaction_date DATE NOT NULL,
        note TEXT,
        FOREIGN KEY (envelope_id) REFERENCES Envelopes(envelope_id) ON DELETE CASCADE
    )
    ''')
    
    # Table 3 : Loans
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Loans (
        loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_name TEXT NOT NULL,
        principal_amount REAL NOT NULL,
        remaining_balance REAL NOT NULL,
        loan_type TEXT CHECK(loan_type IN ('Lent', 'Borrowed')) NOT NULL,
        created_at DATE NOT NULL
    )
    ''')
    
    seed_system_envelopes(cursor)
    
    conn.commit()
    
    conn.close()
    print("System OS: Database architecture compiled and locked.")
    
if __name__ == "__main__":
    initialize_database()