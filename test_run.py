import sqlite3
from datetime import date
from data_models import TransactionModel, TaskModel
from backend_db import save_transaction, DB_PATH, create_task, complete_task
from analytical_engine import run_predictive_engine
from csv_importer import ingest_csv
from report_generation import generate_transaction_ledger
import os

def test_task_tracker():
    print("\n--- Initiating Task Tracker Simulation ---")
    
    try:
        
        new_task = TaskModel(
            description="Cancel Netflix Subscription before renewal",
            due_date=date(2026, 4, 15)
        )
        
        if create_task(new_task):
            
            complete_task(1)
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("SELECT description, is_completed FROM Tasks WHERE task_id = 1")
            data = cursor.fetchone()
            conn.close()
            
            print(f"\n--- Disk Verification ---")
            print(f"Target Memory: {data[0]}")
            print(f"Binary State: {data[1]} (Expected: 1)")
            
            if data[1] == 1:
                print("Status: 100% Boolean Translation Verified. Task engine operational.")
                
    except Exception as e:
        print(f"System Failure: {e}")
        
if __name__ == "__main__":
    test_task_tracker()