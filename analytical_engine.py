import sqlite3
import pandas as pd
from datetime import datetime
import calendar
from backend_db import DB_PATH

def run_predictive_engine(envlope_id: int) -> str:
    """Calculates linear burn rate to predict end-of-month envelope bankruptcy."""
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        
        query = '''
            SELECT amount, transaction_date
            FROM Transactions
            WHERE envelope_id = ?
            AND strftime('%Y-%m', transaction_date) = strftime('%Y-%m', 'now')
        '''
        
        df = pd.read_sql_query(query, conn, params=(envlope_id,))
        
        cursor = conn.cursor()
        cursor.execute("SELECT name, current_balance FROM Envelopes WHERE envelope_id = ?", (envlope_id,))
        env_data = cursor.fetchone()
        
        if not env_data:
            return f"System Alert: Target ID {envlope_id} does not exist."
        
        name, current_balance = env_data
                
        if df.empty:
            return f"System OS: [{name}] 0 bytes of transaction data this month."
        
        today = datetime.today()
        
        days_elapsed = today.day if today.day > 1 else 1
        
        _, total_days_in_month = calendar.monthrange(today.year, today.month)
        days_remaining = total_days_in_month - days_elapsed
        
        total_spent = df['amount'].sum()
        daily_burn_rate = total_spent / days_elapsed
        projected_future_rate = daily_burn_rate * days_remaining
        predicted_final_balance = current_balance - projected_future_rate
        
        report = f"\n--- Predictive Analysis: [{name}] ---\n"
        report += f"Current Balance: ₹{current_balance:.2f}\n"
        report += f"Velocity: Burning ₹{daily_burn_rate:.2f}\n"
        report += f"Projected EOM Balance: ₹{predicted_final_balance:.2f}\n"
        
        if predicted_final_balance < 0:
            report += f">> STATUS RED: At current velocity, envelope will overdraw by ₹{abs(predicted_final_balance):.2f}. <<"
        else:
            report += ">> STATUS GREEN: Trajectory safe. <<"
        
        return report
    
    finally:
        conn.close()