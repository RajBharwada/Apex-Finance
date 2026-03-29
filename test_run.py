import sqlite3
from datetime import date
from data_models import TransactionModel
from backend_db import save_transaction, DB_PATH
from analytical_engine import run_predictive_engine
from csv_importer import ingest_csv

def test_csv_pipeline():
    
    success = ingest_csv('bank_statement.csv')
    
    if success:
        print("\n--- Disk Verification ---")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT current_balance FROM Envelopes WHERE envelope_id = 1")
        master_balance = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Transactions")
        tx_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"Total Transactions Logged: {tx_count}")
        print(f"Master Pool Balance: ${master_balance:.2f}")

        
if __name__ == "__main__":
    test_csv_pipeline()