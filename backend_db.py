import sqlite3
import pandas as pd
from pathlib import Path
import datetime
from data_models import TransactionModel, LoanModel, LoanRepaymentModel, IncomeAllocationModel, TaskModel

sqlite3.register_adapter(datetime.date, lambda val: val.isoformat())

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
        ''', (transaction.envelope_id, transaction.amount, str(transaction.transaction_date), transaction.note))
        
        cursor.execute('''
            UPDATE Envelopes
            SET current_balance = current_balance - ?
            WHERE envelope_id = ?
        ''', (transaction.amount, transaction.envelope_id))
        
        cursor.execute("SELECT current_balance FROM Envelopes WHERE envelope_id = ?",  (transaction.envelope_id,))
        new_balance = cursor.fetchone()[0]
        
        if new_balance < 0 and transaction.envelope_id != 1:
            deficit = abs(new_balance)
            
            cursor.execute('''
                UPDATE Envelopes
                SET current_balance = current_balance - ?
                WHERE envelope_id = 1
            ''', (deficit,))
            
            cursor.execute('''
                UPDATE Envelopes
                SET current_balance = current_balance + ?
                WHERE envelope_id = ?
            ''', (deficit, transaction.envelope_id))
            print(f"System OS: Deficit detected. Auto-transferred ${deficit:.2f} from the Master Pool.")
        
        conn.commit()
        print(f"System OS: Transaction of ${transaction.amount} securely written to disk")
        return True
        
    except sqlite3.Error as e:
        print(f"System Alert: Database integrity error - {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()
        
def create_loan(loan: LoanModel) -> bool:
    """Logs a new Peer-to-Peer debt into the isolated ledger."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO Loans (person_name, principal_amount, remaining_balance, loan_type, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            loan.person_name,
            loan.principal_amount,
            loan.principal_amount,
            loan.loan_type,
            str(loan.created_at)
        ))
        
        conn.commit()
        print(f"System OS: IOU secured. {loan.loan_type} ${loan.principal_amount:.2f}, with {loan.person_name}.")
        return True
    
    except sqlite3.Error as e:
        print(f"System Alert: Loan ledger integrity error - {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()
        
def repay_loan(repayment: LoanRepaymentModel) -> bool:
    """Process a repayment against an existing IOU and mathematically prevents over-pay."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        cursor.execute("SELECT remaining_balance, person_name, loan_type FROM Loans WHERE loan_id = ?", (repayment.loan_id,))
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"Loan ID {repayment.loan_id} does not exist in the database.")
        
        current_balance, person_name, loan_type = result
        
        if repayment.amount > current_balance:
            raise ValueError(f"Integrity Error: Repayment of ${repayment.amount:.2f} exceeds {person_name}'s remaining balance of ${current_balance:.2f}.")
        
        cursor.execute('''
            UPDATE Loans
            SET remaining_balance = remaining_balance - ?
            WHERE loan_id = ?
        ''', (repayment.amount, repayment.loan_id))
        
        conn.commit()
        print(f"System OS: Repayment processed. ${repayment.amount:.2f} safely deducted from {person_name}'s ledger.")
        return True
    
    except Exception as e:
        print(f"System Alert: Repayment failure - {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()
        
def distribute_income(payload: IncomeAllocationModel) -> bool:
    """Executes an atomic multi-table write to distribute funds."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        for envelope_id, amount in payload.allocation.items():
            
            cursor.execute('''
                UPDATE Envelopes
                SET allocated_amount = allocated_amount + ?,
                    current_balance = current_balance + ?
                WHERE envelope_id = ?
            ''', (amount, amount, envelope_id))
            
            if cursor.rowcount == 0:
                raise ValueError(f"Integrity Error: Envelope ID {envelope_id} does not exist.")
            
        conn.commit()
        print(f"System OS: Successfully allocated funds across {len(payload.allocation)} envelopes.")
        return True
    
    except Exception as e:
        print(f"System Alert: Allocation failed - {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

def create_task(task: TaskModel) -> bool:
    """Logs a new actionable financial task into the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO Tasks (description, due_date)
            VALUES (?, ?)
        ''', (task.description, str(task.due_date) if task.due_date else None))
        
        conn.commit()
        print(f"System OS: Task secured -> '{task.description}'")
        return True
    
    except sqlite3.Error as e:
        print(f"System Alert: Task write failure - {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()
        
def complete_task(task_id: int) -> bool:
    """Flips the binary state of a task to True (1)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE Tasks
            SET is_completed = 1
            WHERE task_id = ?
        ''', (task_id,))
        
        if cursor.rowcount == 0:
            raise ValueError(f"Task ID {task_id} does not exist.")
        
        conn.commit()
        print(f"System OS: Task ID {task_id} marked as COMPLETE.")
        return True
    
    except Exception as e:
        print(f"System Alert: Task update failure - {e}")
        conn.rollback()
        return False
    
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
        