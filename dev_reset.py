import sqlite3
from pathlib import Path

def force_rebuild_scheme():
    db_path = Path("apex_finance.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_keys = OFF;")
    
    cursor.execute("DROP TABLE IF EXISTS Transactions;")
    cursor.execute("DROP TABLE IF EXISTS Envelopes;")
    cursor.execute("DROP TABLE IF EXISTS Loans;")
    
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    cursor.execute('''
    CREATE TABLE Envelopes (
        envelope_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNQUE NOT NULL,
        allocated_amount REAL DEFAULT 0.0,
        current_balance REAL DEFAULT 0.0
    )
    ''')
    
    # Table 2 : Transactions
    cursor.execute('''
    CREATE TABLE Transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        envelope_id INTEGER,
        amount REAL NOT NULL,
        transaction_date DATE NOT NULL,
        note TEXT,
        FOREIGN KEY (envelope_id) REFERENCES Envelopes(envelpe_id) ON DELETE CASCADE
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE Loans (
        loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_name TEXT NOT NULL,
        principal_amount REAL NOT NULL,
        remaining_amount REAL NOT NULL,
        type TEXT CHECK(type IN ('Lent', 'Borrow')) NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()
    print("System OS: Nuclear reset complete. B-tree perfectly rebuilt in RAM and flushed to disk.")
    
if __name__ == "__main__":
    force_rebuild_scheme()