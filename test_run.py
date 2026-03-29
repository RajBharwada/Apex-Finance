import sqlite3
from datetime import date
from data_models import TransactionModel
from backend_db import save_transaction, DB_PATH
from analytical_engine import run_predictive_engine

def seed_envelope_and_spend():
    print("\n--- Seeding Data for Predictive Engine")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE Envelopes SET current_balance = 500.00 WHERE envelope_id = 1")
    
    cursor.execute("INSERT OR IGNORE INTO Envelopes (envelope_id, name, allocated_amount, current_balance) VALUES (3, 'Groceries', 100.0, 100.0)")
    conn.commit()
    conn.close()
    
    for i in range(3):
        tx = TransactionModel(
            envelope_id=3,
            amount=15.00,
            transaction_date=date.today(),
            note=f"Simulated grocery run {i+1}"
        )
        save_transaction(tx)
        
def test_prediction():
    print("\n--- Firing Pandas Engine ---")
    result = run_predictive_engine(3)
    print(result)


        
if __name__ == "__main__":
    seed_envelope_and_spend()
    test_prediction()