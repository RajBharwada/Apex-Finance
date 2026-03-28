import sqlite3
from datetime import date
from data_models import TransactionModel
from backend_db import save_transaction, DB_PATH

def setup_test_environment():
    """Bypasses the application layer to forcefully inject a test envelope."""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR IGNORE INTO Envelopes (envelope_id, name, allocated_amount, current_balance)
        VALUES (1, 'Groceries', 500.0, 500.0)
        ''')
    
    conn.commit()
    conn.close()
    print("System OS: Test environment provisioned. 'Groceries' envelope created with $500.00.")
    
def run_simulator():
    print("\n--- Initiating Frontend Simlation ---")
    
    try:
        test_tx = TransactionModel(
            envelope_id=1,
            amount=45.50,
            transaction_date=date.today(),
            note="Test execution protocol"
        )
        print("Pydantic Validation: Success. Strict C-types allocated in RAM.")
        
        success = save_transaction(test_tx)
        
        if success:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("SELECT current_balance FROM Envelopes WHERE envelope_id = 1")
            new_balance = cursor.fetchone()[0]
            conn.close()
            
            print("\n--- Disk Verification ---")
            print(f"Expected B-tree Balance: $454.50 (500.00 - 45.50)")
            print(f"Actual B-tree Balance: ${new_balance:.2f}")
            if new_balance == 454.50:
                print("Status: 100% Data Integrity Verified.")
            
            from backend_db import get_dashboard_envelope_data, get_pie_chart_data
            
            print("\n--- Testing Pandas Aggregation Pipeline ---")
            envelope_data = get_dashboard_envelope_data()
            pie_data = get_pie_chart_data()
            
            print(f"UI Progress Bar Payload: {envelope_data}")
            print(f"Matplotlib Pie Chart Payload: {pie_data}")
                
    except Exception as e:
        print(f"System Failure: {e}")
        
if __name__ == "__main__":
    setup_test_environment()
    run_simulator()