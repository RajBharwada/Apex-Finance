import sqlite3
from pathlib import Path
from data_models import TransactionModel

DB_PATH = Path("apex_finance.db")

def save_transaction(transaction: TransactionModel) -> bool:
    """Executes a secure, atomic write to the SQLite database."""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        cursor.execute('''
            INSERT INTO Transaction (envelope_id, amount, transaction_date, note)
            VALUES (?, ?, ?, ?)
        ''', (transaction.envelope_id, transaction.amount, transaction.transaction_date, transaction.note))
        
        cursor.execute('''
            UPDATE Envelopes
            SET current_balance = current_balance - ?
            WHERE envelope_id = ?
        ''', (transaction.amount, transaction.envelope_id))
        
        conn.commit()
        print(f"System OS: Transaction of ${transaction.amount} securely written to disk")
        return True
        
    except sqlite3.Error as e:
        print(f"System Alert: Database integrity error - {e}")
        
    finally:
        conn.close()