import customtkinter as ctk
import sqlite3
from datetime import date
from backend_db import DB_PATH, save_transaction, distribute_income, get_recent_transactions, delete_transaction, create_task, complete_task, get_active_tasks
from data_models import TransactionModel, IncomeAllocationModel, TaskModel

# UI Config
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ApexFinanceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window
        self.title("Apex Finance OS")
        self.geometry("1000x600")
        self.minsize(800, 500)
        
        # The Grid Matrix
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # The Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.rowconfigure(4, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="APEX OS", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))
        
        # Dashboard Button
        self.btn_dashboard = ctk.CTkButton(self.sidebar, text="Dashboard", command=self.open_dashboard)
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)
        
        # Task Button
        self.btn_tasks = ctk.CTkButton(self.sidebar, text="Task Tracker", command=self.open_tasks)
        self.btn_tasks.grid(row=2, column=0, padx=20, pady=10)
        
        # The main Content Area
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        # Initialize the dashboard by default on boot
        self.open_dashboard()
        
    # --- UI Routing Methods ---
    
    def clear_main_frame(self):
        """System Protocol: Purges all active widgets from the main frame memory."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    def open_dashboard(self):
        """Constructs the primary financial telementry screen and input matrix."""
        self.clear_main_frame()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT current_balance FROM Envelopes WHERE envelope_id = 1")
            result = cursor.fetchone()
            # If DB is empty, default to 0.00
            master_balance = result[0] if result else 0.00
            
            cursor.execute("SELECT envelope_id, name FROM Envelopes")
            envelopes = cursor.fetchall()
            
            # Translating users choice into integer ID
            self.env_mapping = {name: env_id for env_id, name in envelopes}
            env_names = list(self.env_mapping.keys())
            
        except sqlite3.Error:
            master_balance = 0.00
            self.env_mapping = {"Master Pool": 1}
            env_names = ["Master Pool"]
            
        finally:
            conn.close()
            
        # UI - Header
        title = ctk.CTkLabel(self.main_frame, text="Command Center", font=ctk.CTkFont(size=28, weight="bold"))
        title.pack(pady=(30,10), anchor="w", padx=40)
        
        # UI - Master Pool
        balance_card = ctk.CTkFrame(self.main_frame, fg_color="#1e1e1e", corner_radius=15)
        balance_card.pack(pady=20, padx=40, fill="x")
        
        lbl_pool = ctk.CTkLabel(balance_card, text="MASTER POOL BALANCE", font=ctk.CTkFont(size=12), text_color="#6b7280")
        lbl_pool.pack(pady=(20, 0))
        
        # Formatting float
        lbl_balance = ctk.CTkLabel(balance_card, text=f"${master_balance:.2f}", font=ctk.CTkFont(size=56, weight="bold"), text_color="#00ffcc")
        lbl_balance.pack(pady=(0, 20))
        
        # --- Transaction Module ---
        form_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        form_frame.pack(pady=10, padx= 40, fill="x")
        
        form_title = ctk.CTkLabel(form_frame, text="LOG TRANSACTION", font=ctk.CTkFont(size=12, weight="bold"), text_color="#6b7280")
        form_title.pack(anchor="w", pady=(0, 10))
        
        # Input Grid
        input_grid = ctk.CTkFrame(form_frame, fg_color="transparent")
        input_grid.pack(fill="x", pady=5)
        
        # --- Transaction Type Toggle ---
        self.tx_type_var = ctk.StringVar(value="Expense")
        self.type_toggle = ctk.CTkSegmentedButton(
            input_grid, 
            values=["Expense", "Income"],
            variable=self.tx_type_var,
            selected_color="#00ffcc",
            selected_hover_color="#00ccaa",
            unselected_color="#333333",
            text_color="black",
        )
        self.type_toggle.pack(side="left", padx=(0, 10), fill="x")
        
        # Envelope Dropdown
        self.env_var = ctk.StringVar(value=env_names[0])
        self.dropdown = ctk.CTkOptionMenu(input_grid, variable=self.env_var, values=env_names, fg_color="#333333", button_color="#444444")
        self.dropdown.pack(side="left", padx=(0, 10), expand=True, fill="x")
        
        # Amount Entry
        self.amount_entry = ctk.CTkEntry(input_grid, placeholder_text="Amount (e.g. 15.00)", width=120)
        self.amount_entry.pack(side="left", padx=(0, 10), expand=True, fill="x")
        
        # Note Entry
        self.note_entry = ctk.CTkEntry(input_grid, placeholder_text="Transaction Note...", width=200)
        self.note_entry.pack(side="left", padx=(0, 10), expand=True, fill="x")
        
        # Submit Button
        self.btn_submit = ctk.CTkButton(input_grid, text="Execute", fg_color="#00ffcc", text_color="black", hover_color="#00ccaa", font=ctk.CTkFont(weight="bold"), command=self.process_transaction)
        self.btn_submit.pack(side="left", fill="x")
        
        # Status Label (For error/ success messages)
        self.status_lbl = ctk.CTkLabel(form_frame, text="", font=ctk.CTkFont(size=12))
        self.status_lbl.pack(anchor="w", pady=10)
        
        # Live Ledger UI
        
        ledger_title = ctk.CTkLabel(self.main_frame, text="TRANSACTION TAPE", font=ctk.CTkFont(size=12, weight="bold"), text_color="#6b7280")
        ledger_title.pack(anchor="w", padx=40, pady=(10, 0))
        
        self.ledger_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="#1e1e1e", corner_radius=10, height=200)
        self.ledger_frame.pack(pady=10, padx=40, fill="both", expand=True)
        
        transactions = get_recent_transactions()
        
        if not transactions:
            empty_lbl = ctk.CTkLabel(self.ledger_frame, text="No transactions logged yet.", text_color="gray")
            empty_lbl.pack(pady=20)
            
        else:
            for tx in transactions:
                tx_id, tx_date, env_name, amount, note = tx
                
                is_income = note.startswith("INCOME:") or note.startswith("CSV INCOME:")
                amt_color = "#00ffcc" if is_income else "#ff4444"
                prefix = "+" if is_income else "-"
                
                row = ctk.CTkFrame(self.ledger_frame, fg_color="transparent")
                row.pack(fill="x", pady=5)
                
                lbl_date = ctk.CTkLabel(row, text=tx_date, width=90, anchor="w", text_color="#a3a3a3")
                lbl_date.pack(side="left", padx=(10, 5))
                
                lbl_env = ctk.CTkLabel(row, text=env_name, width=120, anchor="w", font=ctk.CTkFont(weight="bold"))
                lbl_env.pack(side="left", padx=5)
                
                lbl_amt = ctk.CTkLabel(row, text=f"{prefix}${amount:,.2f}", width=90, anchor="e", text_color=amt_color, font=ctk.CTkFont(weight="bold"))
                lbl_amt.pack(side="left", padx=5)
                
                lbl_note = ctk.CTkLabel(row, text=note, width=200, anchor="w", text_color="#6b7280")
                lbl_note.pack(side="left", padx=10, expand=True, fill="x")
                
                # The kill switch [X]
                btn_del = ctk.CTkButton(row, text="X", width=30, fg_color="#333333", hover_color="#ff4444", text_color="white", command=lambda t_id=tx_id: self.execute_delete(t_id))
                btn_del.pack(side="right", padx=(5, 10))
                
        
    def process_transaction(self):
        """Execute UI string, translate types, and pushes to the backend database."""
        raw_amt = self.amount_entry.get()
        note_txt = self.note_entry.get()
        selected_env_name = self.env_var.get()
        tx_type = self.tx_type_var.get()
        
        try:
            amt_float = float(raw_amt)
            env_id = self.env_mapping[selected_env_name]
            
            if tx_type == "Expense":
                tx = TransactionModel(
                    envelope_id=env_id,
                    amount=amt_float,
                    transaction_date=date.today(),
                    note=note_txt
                )
                success = save_transaction(tx)
                
            elif tx_type == "Income":
                payload = IncomeAllocationModel(allocation={env_id: amt_float})
                success = distribute_income(payload)
                
                if success and note_txt:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO Transactions (envelope_id, amount, transaction_date, note)
                        VALUES (?, ?, ?, ?)
                    ''', (env_id, amt_float, str(date.today()), f"INCOME: {note_txt}"))
                    conn.commit()
                    conn.close
            
            if success:
                self.open_dashboard()
            else:
                self.status_lbl.configure(text="System Alert: Backend write failed.", text_color="red")
                
        except ValueError:
            self.status_lbl.configure(text="System Alert: Amount must be a valid number.", text_color="red")
    
    def execute_delete(self, tx_id):
        """Bridge command to trigger the Database and reboot the UI."""
        if delete_transaction(tx_id):
            self.open_dashboard()
            
        else:
            self.status_lbl.configure(text=f"System Alert: Fialed to delete TX {tx_id}", text_color="red")
        
    def open_tasks(self):
        """Constructs the Task Tracker visual matrix."""
        self.clear_main_frame()
        
        title = ctk.CTkLabel(self.main_frame, text="Active Objectives", font=ctk.CTkFont(size=28, weight="bold"))
        title.pack(pady=(30, 10), anchor="w", padx=40)
        
        input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        input_frame.pack(pady=10, padx=40, fill="x")
        
        self.task_entry = ctk.CTkEntry(input_frame, placeholder_text="Enter new objective...", width=300)
        self.task_entry.pack(side="left", padx=(0, 10), expand=True, fill="x")
        
        btn_add_task = ctk.CTkButton(input_frame, text="Add Task", fg_color="#00ffcc", text_color="black", hover_color="#00ccaa", font=ctk.CTkFont(weight="bold"), command=self.execute_add_task)
        btn_add_task.pack(side="left")
        
        self.task_status_label = ctk.CTkLabel(self.main_frame, text="", font=ctk.CTkFont(size=12))
        self.task_status_label.pack(anchor="w", padx=40)
        
        self.task_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="#1e1e1e", corner_radius=10)
        self.task_frame.pack(pady=10, padx=40, fill="both", expand=True)
        
        tasks = get_active_tasks()
        
        if not tasks:
            empty_lbl = ctk.CTkLabel(self.task_frame, text="All objective complete. System nominal.", text_color="#6b7280")
            empty_lbl.pack(pady=20)
        else:
            for t in tasks:
                t_id, desc, due = t
                
                row = ctk.CTkFrame(self.task_frame, fg_color="transparent")
                row.pack(fill="x", pady=5)
                
                # Binary Checkbox
                chk = ctk.CTkCheckBox(
                    row,
                    text=desc,
                    font=ctk.CTkFont(size=14),
                    text_color="#a3a3a3",
                    hover_color="#00ffcc",
                    command=lambda id=t_id: self.execute_complete_task(id)
                )
                chk.pack(side="left", padx=10, pady=5)
                
# --- Task Tracker Execution Bridges ---

    def execute_add_task(self):
        """Bridge to translate UI text and inject a new task into the B-tree."""
        desc = self.task_entry.get()
        if not desc:
            self.task_status_label.configure(text="System Alert: Task desription required.", text_color="red")
            return
        
        try:
            new_task = TaskModel(description=desc)
            
            if create_task(new_task):
                self.open_tasks()
            else:
                self.task_status_label.configure(text="System Alert: Backend write failed.", text_color="red")
        
        except ValueError as e:
            self.task_status_label.configure(text=f"Validation Error: {e}", text_color="red")
            
    def execute_complete_task(self, task_id):
        """Bridge to flip the binary state to True (1) and purge from the active UI."""
        if complete_task(task_id):
            self.open_tasks()
        
if __name__ == "__main__":
    app = ApexFinanceApp()
    app.mainloop()