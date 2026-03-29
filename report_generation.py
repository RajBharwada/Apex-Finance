import sqlite3
import pandas as pd
from datetime import datetime
from backend_db import DB_PATH
import os

def generate_transaction_ledger() -> str:
    """Extracts a fully joined transaction ledger including notes and compiles to CSV."""
    print("\n--- Initiating Pandas Ledger Compiler ---")
    conn = sqlite3.connect(DB_PATH)
    
    try:
        
        query = '''
            SELECT
                t.transaction_date AS Date,
                e.name AS Category,
                t.amount AS Amount,
                t.note AS Notes
            FROM Transactions t
            JOIN Envelopes e ON t.envelope_id = e.envelope_id
            ORDER BY t.transaction_date DESC
        '''
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("System Alert: 0 transactions found. No report generated.")
            return ""
        timestamp = datetime.now().strftime("%Y_%m_%d_%H%M")
        filename = f"Apex_Detailed_Ledger_{timestamp}.csv"
        
        df.to_csv(filename, index=False)
        
        file_size = os.path.getsize(filename)
        print(f"System OS: Ledger compiled successfully ({file_size} bytes).")
        
        return filename
    
    except Exception as e:
        print(f"System Alert: Ledger generation failed - {e}")
        return ""
    
    finally:
        conn.close()
        