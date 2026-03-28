import sqlite3
import pandas as pd
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
            INSERT INTO Transactions (envelope_id, amount, transaction_date, note)
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
        

def get_dashboard_envelope_data() -> dict:
    """Reads B-tree state and returns formatting for the UI progress bars."""
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT name, allocated_amount, current_balance FROM Envelopes", conn)
        
        df['percentage_remaining'] = df.apply(
            lambda row: (row['current_balance'] / row['allocated_amount']) * 100
            if row['allocated_amount'] > 0 else 0,
            axis=1
        )
        
        return df.to_dict(orient='records')
    finally:
        conn.close()
        
def get_pie_chart_data() -> dict:
    """Aggregates transactional math for Matplotlib vetor graphics."""
    conn = sqlite3.connect(DB_PATH)
    try:
        query = '''
            SELECT e.name as category, t.amount
            FROM Transactions t
            INNER JOIN Envelopes e ON t.envelope_id = e.envelope_id
        '''
        
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            return{}
        
        aggregated = df.groupby('category')['amount'].sum()
        
        return aggregated.to_dict()
    finally:
        conn.close()
        