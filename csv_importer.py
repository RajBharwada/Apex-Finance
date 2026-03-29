import sqlite3
import pandas as pd
from data_models import TransactionModel, IncomeAllocationModel
from backend_db import save_transaction, distribute_income
from backend_db import DB_PATH

def ingest_csv(file_path: str) -> bool:
    """ETL Pipeline: Extracts CSV, transforms dirty data, and loads into SQLite B-tree."""
    print(f"\n--- Initiating Pandas Ingestion Pipeline: {file_path} ---")
    
    try:
        
        df = pd.read_csv(file_path)
        
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        
        df['Amount'] = df['Amount'].astype(float)
        
        success_count = 0
        
        for index, row in df.iterrows():
            raw_amt = row['Amount']
            desc = row['Description']
            t_date = row['Date']
            
            if raw_amt < 0:
                # Expense
                tx = TransactionModel(
                    envelope_id=2,
                    amount=abs(raw_amt),
                    transaction_date=t_date,
                    note=f"CSV: {desc}"
                )
                if save_transaction(tx):
                    success_count += 1
                    
            elif raw_amt > 0:
                # Income
                payload = IncomeAllocationModel(allocation={1: raw_amt})
                if distribute_income(payload):
                    
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO Transactions (envelope_id, amount, transaction_date, note)
                        VALUES (?, ?, ?, ?)
                    ''', (1, raw_amt, str(t_date), f"CSV INCOME: {desc}"))
                    conn.commit()
                    conn.close()
                    
                    success_count += 1
                    
        print(f"System OS: Pipeline closed. Successfully injected {success_count} records into the ledger.")
        return True
    
    except Exception as e:
        print(f"System Alert: Pipeline failure - {e}")
        return False