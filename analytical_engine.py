import sqlite3
import pandas as pd
from datetime import datetime
import calendar
from backend_db import DB_PATH

def run_predictive_engine(envelope_id: int) -> str:
    """Calculates linear burn rate and historical velocity to predict envelope bankruptcy."""
    conn = sqlite3.connect(DB_PATH)
    try:
        # 1. Verify Target
        cursor = conn.cursor()
        cursor.execute("SELECT name, current_balance FROM Envelopes WHERE envelope_id = ?", (envelope_id,))
        env_data = cursor.fetchone()
        if not env_data:
            return f"System Alert: Target ID {envelope_id} does not exist."
        name, current_balance = env_data

        # 2. Current Month Matrix
        query_current = '''
            SELECT amount, transaction_date
            FROM Transactions
            WHERE envelope_id = ?
            AND strftime('%Y-%m', transaction_date) = strftime('%Y-%m', 'now')
        '''
        df_current = pd.read_sql_query(query_current, conn, params=(envelope_id,))

        # 3. Historical Matrix (Last Month's Velocity)
        query_prev = '''
            SELECT amount
            FROM Transactions
            WHERE envelope_id = ?
            AND strftime('%Y-%m', transaction_date) = strftime('%Y-%m', 'now', '-1 month')
        '''
        df_prev = pd.read_sql_query(query_prev, conn, params=(envelope_id,))

        today = datetime.today()
        days_elapsed = today.day if today.day > 1 else 1
        _, total_days_in_month = calendar.monthrange(today.year, today.month)
        days_remaining = total_days_in_month - days_elapsed

        # Mathematical Projections
        total_spent_now = df_current['amount'].sum() if not df_current.empty else 0.0
        daily_burn_rate = total_spent_now / days_elapsed
        projected_future_rate = daily_burn_rate * days_remaining
        predicted_final_balance = current_balance - projected_future_rate

        # Historical Comparison
        prev_burn_rate = 0.0
        if not df_prev.empty:
            _, prev_days = calendar.monthrange(today.year, (today.month - 1) or 12)
            prev_burn_rate = df_prev['amount'].sum() / prev_days

        # 4. Generate the Terminal Report
        report = f"--- PREDICTIVE ANALYSIS: [{name.upper()}] ---\n\n"
        report += f"Current Reserve: ₹{current_balance:,.2f}\n"
        report += f"Current Velocity: Burning ₹{daily_burn_rate:,.2f} / day\n"

        if prev_burn_rate > 0:
            trend = ((daily_burn_rate - prev_burn_rate) / prev_burn_rate) * 100
            if trend > 0:
                report += f"Velocity Trend: +{trend:.1f}% acceleration vs last month.\n"
            else:
                report += f"Velocity Trend: {trend:.1f}% deceleration vs last month.\n"

        report += f"\nProjected EOM Balance: ₹{predicted_final_balance:,.2f}\n\n"

        # Threat Assessment Logic
        if current_balance < 0:
            report += ">> STATUS BLACK: Vault is already breached. <<"
        elif predicted_final_balance < 0:
            report += f">> STATUS RED: Trajectory indicates overdraw of ₹{abs(predicted_final_balance):,.2f} by EOM. <<"
        elif predicted_final_balance < (current_balance * 0.1) and current_balance > 0:
            report += ">> STATUS YELLOW: Warning. Slim margin of error for EOM. <<"
        else:
            report += ">> STATUS GREEN: Burn trajectory secure. <<"

        return report

    finally:
        conn.close()