import sqlite3
import pandas as pd
from pathlib import Path
import datetime
from data_models import TransactionModel, LoanModel, LoanRepaymentModel, IncomeAllocationModel, TaskModel
from database_setup import initialize_database

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
        
        for envelope_id, amount in payload.allocations.items():
            
            cursor.execute('''
                UPDATE Envelopes
                SET allocated_amount = allocated_amount + ?,
                    current_balance = current_balance + ?
                WHERE envelope_id = ?
            ''', (amount, amount, envelope_id))
            
            if cursor.rowcount == 0:
                raise ValueError(f"Integrity Error: Envelope ID {envelope_id} does not exist.")
            
        conn.commit()
        print(f"System OS: Successfully allocated funds across {len(payload.allocations)} envelopes.")
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
    """Aggregates transactional math strictly for the CURRENT CALENDAR MONTH."""
    conn = sqlite3.connect(DB_PATH)
    try:
        # strftime('%Y-%m') ensures it only pulls data for the current month and year
        query = '''
            SELECT e.name as category, t.amount
            FROM Transactions t
            INNER JOIN Envelopes e ON t.envelope_id = e.envelope_id
            WHERE e.envelope_id != 1 
            AND t.note NOT LIKE 'SYSTEM:%'
            AND t.note NOT LIKE 'INCOME:%'
            AND strftime('%Y-%m', t.transaction_date) = strftime('%Y-%m', 'now')
        '''
        
        df = pd.read_sql_query(query, conn)
        if df.empty:
            return {}
            
        aggregated = df.groupby('category')['amount'].sum()
        return aggregated.to_dict()
    finally:
        conn.close()

def get_bar_chart_data() -> dict:
    """Aggregates monthly burn rates for the CURRENT YEAR, pre-loading all 12 months."""
    conn = sqlite3.connect(DB_PATH)
    try:
        # Sums up the totals grouped by the exact month of the current year
        query = '''
            SELECT strftime('%m', transaction_date) as month, SUM(amount) as total
            FROM Transactions
            WHERE envelope_id != 1 
            AND note NOT LIKE 'SYSTEM:%'
            AND note NOT LIKE 'INCOME:%'
            AND strftime('%Y', transaction_date) = strftime('%Y', 'now')
            GROUP BY month
        '''
        df = pd.read_sql_query(query, conn)
        
        # Pre-fill all 12 months with $0 so the graph always displays the full year cleanly
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        result = {m: 0.0 for m in months}
        
        # Map SQLite's output ('04') to our labels ('Apr') and inject the real data
        month_map = {'01':'Jan', '02':'Feb', '03':'Mar', '04':'Apr', '05':'May', '06':'Jun', 
                     '07':'Jul', '08':'Aug', '09':'Sep', '10':'Oct', '11':'Nov', '12':'Dec'}
                     
        for _, row in df.iterrows():
            label = month_map.get(row['month'])
            if label:
                result[label] = row['total']
                
        return result
    finally:
        conn.close()

def get_recent_transactions(limit: int = 50) -> list:
    """System Protocol: Pulls the 50 most recent transactions with relational JOIN."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT t.transaction_id, t.transaction_date, e.name, t.amount, t.note
            FROM Transactions t
            JOIN Envelopes e ON t.envelope_id = e.envelope_id
            ORDER BY t.transaction_date DESC, t.transaction_id DESC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    except sqlite3.Error as e:
        print(f"System Alert: Ledger query failed - {e}")
        return []
    
    finally:
        conn.close()
    
def delete_transaction(transaction_id: int) -> bool:
    """Executes an Atomic Mathematical Refund and hard-deletes the paper trail."""    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        cursor.execute("SELECT envelope_id, amount, note FROM Transactions WHERE transaction_id = ?", (transaction_id,))
        result = cursor.fetchone()
        
        if not result:
            raise ValueError(f"Integrity Error: Transaction ID {transaction_id} does not exist.")
        
        env_id, amount, note = result
        
        is_income = note.startswith("INCOME:") or note.startswith("CSV INCOME:")
        
        if is_income:
            cursor.execute('''
            UPDATE Envelopes
            SET current_balance = current_balance - ?,
                allocated_amount = allocated_amount - ?
            WHERE envelope_id = ?
        ''', (amount, env_id))
            
        else:
            cursor.execute('''
                UPDATE Envelopes
                SET current_balance = current_balance + ?
                WHERE envelope_id = ?
            ''', (amount, env_id))
            
        cursor.execute("DELETE FROM Transactions WHERE transaction_id = ?", (transaction_id,))
        
        conn.commit()
        print(f"System OS: Transaction {transaction_id} purged. ${amount} refunded successfully.")
        return True
    
    except Exception as e:
        print(f"System Alert: Atomic deletion failed - {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()
        
def get_active_tasks() -> list:
    """System Protocol: Pulls all incomplete tasks (Binary 0) from the B-tree."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT task_id, description, due_date
            FROM Tasks
            WHERE is_completed = 0
            ORDER BY task_id DESC
        ''')
        return cursor.fetchall()
    
    except sqlite3.Error as e:
        print(f"System Alert: Task query failed - {e}")
        return []
    
    finally:
        conn.close()

def seed_default_categories():
    """System Protocol: Injects baseline categories if they do not exists."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    defaults = ["Food", "Travelling", "Entertainment"]
    
    try:
        for name in defaults:
            cursor.execute('''
                INSERT OR IGNORE INTO Envelopes (name, allocated_amount, current_balance)
                VALUES (?, 0.0, 0.0)
            ''', (name,))
        conn.commit()
    
    except sqlite3.Error as e:
        print(f"System Alert: Default seeding failed - {e}")
        
    finally:
        conn.close()
        
def add_custom_envelope(name: str) -> bool:
    """System Protocol: Allocates a new custom envelope in the B-tree."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO Envelopes (name, allocated_amount, current_balance)
            VALUES (?, 0.0, 0.0)
        ''', (name.strip(),))
        conn.commit()
        return True
    
    except sqlite3.IntegrityError:
        return False
    
    finally:
        conn.close()

def delete_custom_envelope(env_id: int, env_name: str) -> bool:
    """System Protocol: Bulletproof Merge & Purge. Refunds all columns dynamically."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT envelope_id FROM Envelopes WHERE name = 'Master Pool'")
        master_result = cursor.fetchone()
        if not master_result:
            raise ValueError("Fatal Error: Master Pool missing from database.")
        master_id = master_result[0]

        if env_id == master_id:
            print("System Alert: Core system envelope cannot be deleted.")
            return False

        cursor.execute("SELECT current_balance, allocated_amount FROM Envelopes WHERE envelope_id = ?", (env_id,))
        result = cursor.fetchone()
        if not result:
            raise ValueError("Integrity Error: Envelope does not exist.")
            
        curr_bal = result[0] or 0.0
        alloc_amt = result[1] or 0.0
        print(f"System OS: Intercepted '{env_name}' -> Balance: ${curr_bal} | Allocated: ${alloc_amt}")

        cursor.execute('''
            UPDATE Envelopes 
            SET current_balance = current_balance + ?,
                allocated_amount = allocated_amount + ?
            WHERE envelope_id = ?
        ''', (curr_bal, alloc_amt, master_id))

        archive_note = f" [Archived from: {env_name}]"
        cursor.execute('''
            UPDATE Transactions 
            SET envelope_id = ?, note = note || ?
            WHERE envelope_id = ?
        ''', (master_id, archive_note, env_id))
        
        cursor.execute("DELETE FROM Envelopes WHERE envelope_id = ?", (env_id,))
        
        conn.commit()
        print(f"System OS: Purge complete. Refunded to Master Pool (ID {master_id}).")
        return True
        
    except Exception as e:
        print(f"System Alert: Merge & Purge failed - {e}")
        conn.rollback() 
        return False
        
    finally:
        conn.close()

def execute_factory_reset() -> bool:
    """System Protocol: Drops all tables to wipe memory, then rebuilds fatory schema.""" 
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DROP TABLE IF EXISTS Transactions")
        cursor.execute("DROP TABLE IF EXISTS Envelopes")
        cursor.execute("DROP TABLE IF EXISTS Tasks")
        cursor.execute("DROP TABLE IF EXISTS Loans")
        conn.commit()
        
        initialize_database()
        seed_default_categories()
        print("System OS: Factory reset completed. Matrix reinitialized.")
        return True
    
    except Exception as e:
        print(f"System Alert: Factory reset failed - {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()
        
def update_category_principal(env_id: int, new_principal: float) -> bool:
    """System Protocol: Updates the static Principal Target for a category."""

    if env_id == 1:
        print("System Alert: Cannot set a target for the Master Pool.")
        return False
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        
        cursor.execute("UPDATE Envelopes SET allocated_amount = ? WHERE envelope_id = ?", (new_principal, env_id))
        conn.commit()
        print(f"System OS: Principal Target for Envelope {env_id} locked at ${new_principal:.2f}")
        return True
    
    except Exception as e:
        
        print(f"System Alert: Principal update failed - {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

def execute_monthly_replenish() -> tuple[bool, str]:
    """System Protocol: Auto-funds all categories to their targets IF Master Pool is sufficient."""
    
    import datetime
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Check Master pool
        cursor.execute("SELECT current_balance FROM Envelopes WHERE envelope_id = 1")
        master_result = cursor.fetchone()
        if not master_result:
            return False, "Fatal Error: Master Pool missing."
        master_balance = master_result[0]

        # 2. check for the amount shortage
        cursor.execute("SELECT envelope_id, name, allocated_amount, current_balance FROM Envelopes WHERE envelope_id != 1")
        categories = cursor.fetchall()
        
        total_required = 0.0
        replenish_plan = []
        
        for env_id, name, principal, current in categories:
            # adds only if amt is less then principle
            if principal > current:
                needed = principal - current
                total_required += needed
                replenish_plan.append((env_id, name, needed))
                
        if total_required == 0.0:
            return True, "System OS: All vaults are already at or above their Principal targets. No action needed."

        # 3. checks if master pool has enough
        if master_balance < total_required:
            shortfall = total_required - master_balance
            return False, f"System Alert: Master Pool is insufficient. You need ${shortfall:,.2f} more in the Master Pool to complete the cycle."

        # 4. The Distribution
        cursor.execute("PRAGMA foreign_keys = ON;")
        for env_id, name, needed in replenish_plan:
            # Inject cash into category
            cursor.execute("UPDATE Envelopes SET current_balance = current_balance + ? WHERE envelope_id = ?", (needed, env_id))
            
            # Write the paper trail
            cursor.execute('''
                INSERT INTO Transactions (envelope_id, amount, transaction_date, note)
                VALUES (?, ?, ?, ?)
            ''', (env_id, needed, str(datetime.date.today()), f"SYSTEM: Monthly Cycle Replenish (+${needed:.2f})"))

        # 5. Deduct the massive total from the Master Pool
        cursor.execute("UPDATE Envelopes SET current_balance = current_balance - ? WHERE envelope_id = 1", (total_required,))
        
        conn.commit()
        return True, f"System OS: Cycle complete. ${total_required:,.2f} deployed from Master Pool to categories."
        
    except Exception as e:
        conn.rollback()
        return False, f"System Alert: Replenish engine failed - {e}"
    finally:
        conn.close()
        
def add_income_to_master(amount: float, note: str) -> bool:
    """System Protocol: Injects new money directly into the Master Pool."""
    import datetime
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # 1. Add money to Master Pool
        cursor.execute('''
            UPDATE Envelopes
            SET current_balance = current_balance + ?
            WHERE envelope_id = 1
        ''', (amount,))
        
        # 2. Log it on the transaction tape
        final_note = f"INCOME: {note}" if note.strip() else "INCOME: Master Pool Deposit"
        cursor.execute('''
            INSERT INTO Transactions (envelope_id, amount, transaction_date, note)
            VALUES (1, ?, ?, ?)
        ''', (amount, str(datetime.date.today()), final_note))
        
        conn.commit()
        print(f"System OS: ${amount:.2f} securely injected into Master Pool.")
        return True
        
    except Exception as e:
        print(f"System Alert: Income injection failed - {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
        
def get_active_loans() -> list:
    """System Protocol: Pulls all unresolved P2P debts from the ledger."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # We only pull loans that haven't been fully paid off (remaining > 0)
        cursor.execute('''
            SELECT loan_id, person_name, principal_amount, remaining_balance, loan_type
            FROM Loans
            WHERE remaining_balance > 0
            ORDER BY created_at DESC
        ''')
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"System Alert: Debt Ledger query failed - {e}")
        return []
    finally:
        conn.close()
                