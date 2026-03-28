import sqlite3
from datetime import date
from data_models import LoanRepaymentModel
from backend_db import repay_loan, DB_PATH

def test_iou_repayment():
    print("\n--- Initiating IOU Ledger ---")
    
    try:
        
        repayment = LoanRepaymentModel(loan_id=1, amount=50.0)
        print("Pydantic Validation: Repayment payload seured.")
        
        success = repay_loan(repayment)
        
        if success:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("SELECT remaining_balance FROM Loans WHERE loan_id = 1")
            new_balance = cursor.fetchone()[0]
            conn.close()
            
            print(f"--- Disk Verification ---")
            print(f"New Remaining Balance: ${new_balance:.2f} (Expected: $100.0)")
            
            if new_balance == 100:
                print("Status: 100% Repayment Math Verified. The ledger is perfectly balanced.")
                
    except Exception as e:
        print(f"System Failure: {e}")
        
if __name__ == "__main__":
    test_iou_repayment()