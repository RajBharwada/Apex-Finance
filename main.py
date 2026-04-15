import customtkinter as ctk
import sqlite3
import matplotlib.pyplot as plt
from datetime import date
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from backend_db import DB_PATH, save_transaction, distribute_income, get_recent_transactions, delete_transaction, create_task, complete_task, get_active_tasks, add_custom_envelope, delete_custom_envelope, execute_factory_reset, add_income_to_master, update_category_principal, execute_monthly_replenish, get_pie_chart_data, get_bar_chart_data, get_active_loans, create_loan, repay_loan, seed_default_categories, delete_task
from database_setup import initialize_database
from data_models import TransactionModel, IncomeAllocationModel, TaskModel, LoanRepaymentModel, LoanModel
from report_generation import generate_transaction_ledger

# UI Config
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class CustomConfirmDialog(ctk.CTkToplevel):
    """A custom dark theme model that hijacks the UI thread until a decision is made."""
    def __init__(self, title, message):
        super().__init__()
        self.title(title)
        self.geometry("450x250")
        self.resizable(False, False)
        self.configure(fg_color="#1e1e1e")
        
        self.attributes("-topmost", True)
        
        self.result = False
        
        # UI: The Big Red Title
        lbl_title = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(family="Segoe UI",size=20, weight="bold"), text_color="#ff4444")
        lbl_title.pack(pady=(20, 10))
        
        # UI: The Gray Warning Message
        lbl_msg = ctk.CTkLabel(self, text=message, font=ctk.CTkFont(family="Segoe UI",size=14), text_color="#a3a3a3", wraplength=400)
        lbl_msg.pack(pady=(0, 20), padx=20)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        btn_cancel = ctk.CTkButton(btn_frame, text="Cancel", fg_color="#333333", hover_color="#444444", command=self.cancel_action)
        btn_cancel.pack(side="left", expand=True, padx=10)
        
        btn_confirm = ctk.CTkButton(btn_frame, text="INITIATE PURGE", font=ctk.CTkFont(family="Segoe UI",weight="bold"), fg_color="#ff4444", text_color="white", hover_color="#cc0000", command=self.confirm_action)
        btn_confirm.pack(side="right", expand=True, padx=10)
        
        self.wait_visibility()
        self.grab_set()
        self.focus_force()
        
    def confirm_action(self):
        self.result = True
        self.destroy()
        
    def cancel_action(self):
        self.result = False
        self.destroy()
        
    def get_result(self):
        """Halts the main Python thread until this specific window is destroyed."""
        self.wait_window()
        return self.result

class AddIncomeDialog(ctk.CTkToplevel):
    """A custom modal dedicated exclusively to Master Pool fund injections."""
    def __init__(self):
        super().__init__()
        self.title("SYSTEM PROTOCOL: INJECT FUNDS")
        self.geometry("400x300")
        self.resizable(False, False)
        self.configure(fg_color="#1e1e1e")
        self.attributes("-topmost", True)
        
        self.amount = None
        self.note = None
        
        # UI Elements
        lbl = ctk.CTkLabel(self, text="MASTER POOL DEPOSIT", font=ctk.CTkFont(family="Segoe UI",size=20, weight="bold"), text_color="#0A84FF")
        lbl.pack(pady=(20, 10))
        
        self.amt_entry = ctk.CTkEntry(self, placeholder_text="Amount (e.g. 1500)", width=300, height=40)
        self.amt_entry.pack(pady=15)
        
        self.note_entry = ctk.CTkEntry(self, placeholder_text="Note (e.g. Salary, Sold Item)", width=300, height=40)
        self.note_entry.pack(pady=15)
        
        btn = ctk.CTkButton(self, text="AUTHORIZE DEPOSIT", fg_color="#0066CC", text_color="black", hover_color="#0A84FF", font=ctk.CTkFont(family="Segoe UI",weight="bold"), command=self.submit)
        btn.pack(pady=20)
        
        # OS Lockdown Protocol
        self.wait_visibility()
        self.grab_set()
        self.focus_force()

    def submit(self):
        """Captures the data and destroys the UI thread."""
        self.amount = self.amt_entry.get()
        self.note = self.note_entry.get()
        self.destroy()

    def get_input(self):
        """Halts main thread until OS modal is resolved."""
        self.wait_window()
        return self.amount, self.note

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
        
        # The Sidebar Container
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#111111")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.sidebar.grid_rowconfigure(4, weight=0)
        
        # The Logo
        self.logo_label = ctk.CTkLabel(self.sidebar, text="APEX OS", font=ctk.CTkFont(family="Segoe UI",size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))
        
        # Row 1: Dashboard Button
        self.btn_dashboard = ctk.CTkButton(self.sidebar, text="Dashboard", command=self.show_dashboard)
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)
        
        # Row 2: Vault Button 
        self.btn_vaults = ctk.CTkButton(self.sidebar, text="Vault Balances", command=self.show_vaults)
        self.btn_vaults.grid(row=2, column=0, padx=20, pady=10)
        
        # Row 3: Task Button 
        self.btn_tasks = ctk.CTkButton(self.sidebar, text="Task Tracker", command=self.show_tasks)
        self.btn_tasks.grid(row=3, column=0, padx=20, pady=10)

        # Row 4: Telemetry Matrix
        self.btn_telemetry = ctk.CTkButton(self.sidebar, text="Telemetry", command=self.show_telemetry)
        self.btn_telemetry.grid(row=4, column=0, padx=20, pady=10)

        # Row 5: Debt Ledger (NEW)
        self.btn_loans = ctk.CTkButton(self.sidebar, text="Debt Ledger", command=self.show_debt)
        self.btn_loans.grid(row=5, column=0, padx=20, pady=10)
        
        self.sidebar.grid_rowconfigure(5, weight=0)
        self.sidebar.grid_rowconfigure(6, weight=1) 
        
        # Row 7: Settings Button
        self.btn_settings = ctk.CTkButton(self.sidebar, text="Settings", fg_color="#333333", hover_color="#444444", command=self.show_settings)
        self.btn_settings.grid(row=7, column=0, padx=20, pady=(10, 20))
        
       # 1. The Main Content Area MUST be built first
        self.main_container = ctk.CTkFrame(self, corner_radius=15)
        self.main_container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # 2. Initialize Memory stack (Building the frames inside the container)
        self.build_dashboard_frame()
        self.build_task_frame()
        self.build_vault_frame()
        self.build_settings_frame()
        self.build_telemetry_frame()
        self.build_debt_frame()       # <-- IT MUST GO EXACTLY HERE
        
        # 3. Boot into dashboard
        self.show_dashboard()
        
    # --- UI Routing Methods ---
    def hide_all_frames(self):
        """Mathematically unplugs all screens from the renderer."""
        self.dashboard_frame.grid_forget()
        self.task_frame.grid_forget()
        self.vault_frame.grid_forget()
        self.settings_frame.grid_forget()
        self.telemetry_frame.grid_forget()
        self.debt_frame.grid_forget() # NEW

    def show_debt(self):
        self.hide_all_frames()
        self.debt_frame.grid(row=0, column=0, sticky="nsew")
        self.refresh_debt_data()

    def show_telemetry(self):
        self.hide_all_frames()
        self.telemetry_frame.grid(row=0, column=0, sticky="nsew")
        self.refresh_telemetry_data()

    def show_dashboard(self):
        self.hide_all_frames()
        self.dashboard_frame.grid(row=0, column=0, sticky="nsew")
        self.refresh_dashboard_data()
        
    def show_tasks(self):
        self.hide_all_frames()
        self.task_frame.grid(row=0, column=0, sticky="nsew")
        self.refresh_task_data()

    def show_vaults(self):
        self.hide_all_frames()
        self.vault_frame.grid(row=0, column=0, sticky="nsew")
        self.refresh_vault_data()

    def show_settings(self):
        self.hide_all_frames()
        self.settings_frame.grid(row=0, column=0, sticky="nsew")

    def build_dashboard_frame(self):
        """Constructs the static UI matrix for the dashboard ONCE during boot."""
        self.dashboard_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.dashboard_frame.grid(row=0, column=0, sticky="nsew")

        # --- UI Header & Isolated Income Button ---
        header_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=(30, 10))
        
        title = ctk.CTkLabel(header_frame, text="Command Center", font=ctk.CTkFont(family="Segoe UI",size=28, weight="bold"))
        title.pack(side="left")
        
        btn_income = ctk.CTkButton(header_frame, text="+ DEPOSIT TO MASTER POOL", fg_color="#0066CC", text_color="black", hover_color="#0A84FF", font=ctk.CTkFont(family="Segoe UI",weight="bold"), command=self.trigger_income_injection)
        btn_income.pack(side="right")
        
        # --- UI Master Pool Balance ---
        balance_card = ctk.CTkFrame(self.dashboard_frame, fg_color="#1e1e1e", corner_radius=15)
        balance_card.pack(pady=20, padx=40, fill="x")
        
        lbl_pool = ctk.CTkLabel(balance_card, text="MASTER POOL BALANCE", font=ctk.CTkFont(family="Segoe UI",size=12), text_color="#6b7280")
        lbl_pool.pack(pady=(20, 0))
        
        
        self.lbl_balance = ctk.CTkLabel(balance_card, text="₹0.00", font=ctk.CTkFont(family="Segoe UI",size=56, weight="bold"), text_color="#0A84FF")
        self.lbl_balance.pack(pady=(0, 20))
        
        # --- Transaction Module (Expense Only) ---
        form_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        form_frame.pack(pady=10, padx=40, fill="x")
        
        form_title = ctk.CTkLabel(form_frame, text="LOG EXPENSE", font=ctk.CTkFont(family="Segoe UI",size=12, weight="bold"), text_color="#6b7280")
        form_title.pack(anchor="w", pady=(0, 10))
        
        # Dark container for the input elements
        input_container = ctk.CTkFrame(form_frame, fg_color="#1e1e1e", corner_radius=15)
        input_container.pack(fill="x", pady=5)
        
        input_grid = ctk.CTkFrame(input_container, fg_color="transparent")
        input_grid.pack(pady=15, padx=20, fill="x")
        
        self.amount_entry = ctk.CTkEntry(input_grid, placeholder_text="Amount", width=120)
        self.amount_entry.pack(side="left", padx=(0, 10))
        
        self.note_entry = ctk.CTkEntry(input_grid, placeholder_text="What was this for?", width=200)
        self.note_entry.pack(side="left", padx=(0, 10), expand=True, fill="x")
        
        self.env_var = ctk.StringVar(value="Loading...")
        self.dropdown = ctk.CTkOptionMenu(
            input_grid, 
            variable=self.env_var, 
            values=["Loading..."], 
            fg_color="#333333", 
            button_color="#444444",
            command=self.handle_dropdown_selection)
        self.dropdown.pack(side="left", padx=(0, 10), expand=True, fill="x")
        
        self.btn_del_env = ctk.CTkButton(input_grid, text="-", width=30, fg_color="#333333", hover_color="#ff4444", text_color="white", command=self.execute_delete_envelope)
        self.btn_del_env.pack(side="left", padx=(0, 10))
        
        self.btn_submit = ctk.CTkButton(input_grid, text="Execute", fg_color="#0A84FF", text_color="black", hover_color="#0066CC", font=ctk.CTkFont(family="Segoe UI",weight="bold"), command=self.process_transaction)
        self.btn_submit.pack(side="left")
        
        self.status_lbl = ctk.CTkLabel(form_frame, text="", font=ctk.CTkFont(family="Segoe UI",size=12))
        self.status_lbl.pack(anchor="w", pady=5)
        
        # --- Live Ledger UI Container ---
        ledger_title = ctk.CTkLabel(self.dashboard_frame, text="TRANSACTION TAPE", font=ctk.CTkFont(family="Segoe UI",size=12, weight="bold"), text_color="#6b7280")
        ledger_title.pack(anchor="w", padx=40, pady=(10, 0))
        
        self.ledger_frame = ctk.CTkScrollableFrame(self.dashboard_frame, fg_color="#1e1e1e", corner_radius=15, height=200)
        self.ledger_frame.pack(pady=10, padx=40, fill="both", expand=True)

    def trigger_income_injection(self):
        """Summons the custom modal and routes funds strictly to the Master Pool."""
        dialog = AddIncomeDialog()
        raw_amt, raw_note = dialog.get_input()
        
        if raw_amt:
            try:
                amt_float = float(raw_amt)
                if add_income_to_master(amt_float, raw_note):
                    self.status_lbl.configure(text="System OS: Master Pool funded successfully.", text_color="#0A84FF")
                    self.refresh_dashboard_data()
            except ValueError:
                self.status_lbl.configure(text="System Alert: Invalid income amount.", text_color="red")

    def refresh_dashboard_data(self):
        """Silently queries the database and updates only the text and list items."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT current_balance FROM Envelopes WHERE name = 'Master Pool'")
            result = cursor.fetchone()
            master_balance = result[0] if result else 0.00
            
            cursor.execute("SELECT envelope_id, name FROM Envelopes")
            envelopes = cursor.fetchall()
            self.env_mapping = {name: env_id for env_id, name in envelopes}
            env_names = list(self.env_mapping.keys())
            env_names.append("+ Add New Category...")
        except sqlite3.Error:
            master_balance = 0.00
            env_names = ["Master Pool"]
        finally:
            conn.close()

        # Update Live Text
        self.lbl_balance.configure(text=f"₹{master_balance:,.2f}")
        
        # Update Dropdown
        self.dropdown.configure(values=env_names)
        if self.env_var.get() not in env_names:
            self.env_var.set(env_names[0])

        # Purge and Rebuild ONLY the Ledger Rows
        for widget in self.ledger_frame.winfo_children():
            widget.destroy()

        transactions = get_recent_transactions()
        if not transactions:
            ctk.CTkLabel(self.ledger_frame, text="No transactions logged yet.", text_color="gray").pack(pady=20)
        else:
            for tx in transactions:
                tx_id, tx_date, env_name, amount, note = tx
                is_income = note.startswith("INCOME:") or note.startswith("CSV INCOME:")
                amt_color = "#0A84FF" if is_income else "#ff4444"
                prefix = "+" if is_income else "-"

                row = ctk.CTkFrame(self.ledger_frame, fg_color="transparent")
                row.pack(fill="x", pady=5)

                ctk.CTkLabel(row, text=tx_date, width=90, anchor="w", text_color="#a3a3a3").pack(side="left", padx=(10, 5))
                ctk.CTkLabel(row, text=env_name, width=120, anchor="w", font=ctk.CTkFont(family="Segoe UI",weight="bold")).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=f"{prefix}₹{amount:,.2f}", width=90, anchor="e", text_color=amt_color, font=ctk.CTkFont(family="Segoe UI",weight="bold")).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=note, width=200, anchor="w", text_color="#6b7280").pack(side="left", padx=10, expand=True, fill="x")
                ctk.CTkButton(row, text="X", width=30, fg_color="#333333", hover_color="#ff4444", text_color="white", command=lambda t_id=tx_id: self.execute_delete(t_id)).pack(side="right", padx=(5, 10))
                   
    def process_transaction(self):
        """Dedicated execution bridge strictly for logging Category Expenses."""
        raw_amt = self.amount_entry.get()
        note_txt = self.note_entry.get()
        selected_env_name = self.env_var.get()
        
        # 1. Parameter Validation
        if not raw_amt or selected_env_name in ["+ Add New Category...", "Loading..."]:
            self.status_lbl.configure(text="System Alert: Missing transaction parameters.", text_color="red")
            return
            
        try:
            amt_float = float(raw_amt)
            env_id = self.env_mapping[selected_env_name]
            
            # 2. Formulate the Expense Payload
            tx = TransactionModel(
                envelope_id=env_id,
                amount=amt_float,
                transaction_date=date.today(),
                note=note_txt
            )
            
            # 3. Execute backend write
            if save_transaction(tx):
                self.amount_entry.delete(0, 'end')
                self.note_entry.delete(0, 'end')
                self.status_lbl.configure(text="System OS: Expense logged securely.", text_color="#0A84FF")
                self.refresh_dashboard_data()
            else:
                self.status_lbl.configure(text="System Alert: Backend write failed.", text_color="red")
                
        except ValueError:
            self.status_lbl.configure(text="System Alert: Amount must be a valid number.", text_color="red")
    
    def execute_delete(self, tx_id):
        """Bridge command to trigger the Database and reboot the UI."""
        if delete_transaction(tx_id):
            self.refresh_dashboard_data()
            
        else:
            self.status_lbl.configure(text=f"System Alert: Fialed to delete TX {tx_id}", text_color="red")
    
    def handle_dropdown_selection(self, choice):
        """Intercepts the dropdown selection. If it's the trigger, launch the UI dialog."""
        if choice == "+ Add New Category...":
            dialog = ctk.CTkInputDialog(text="Enter new category name:", title="System Allocation")
            new_env_name = dialog.get_input()
            
            if new_env_name and new_env_name.strip():
                if add_custom_envelope(new_env_name):
                    self.status_lbl.configure(text=f"System OS: Category '{new_env_name}' added.", text_color="#0A84FF")
                    self.refresh_dashboard_data()
                    self.env_var.set(new_env_name)
                else:
                    self.status_lbl.configure(text="System Alert: Category already exists.", text_color="red")
                    self.env_var.set(list(self.env_mapping.keys())[0])
            else:
                self.env_var.set(list(self.env_mapping.keys())[0])
    
    def build_task_frame(self):
        """Constructs the Task Tracker visual matrix."""
        self.task_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.task_frame.grid(row=0, column=0, sticky="nsew")
        
        title = ctk.CTkLabel(self.task_frame, text="Active Objectives", font=ctk.CTkFont(family="Segoe UI",size=28, weight="bold"))
        title.pack(pady=(30, 10), anchor="w", padx=40)
        
        input_frame = ctk.CTkFrame(self.task_frame, fg_color="transparent")
        input_frame.pack(pady=10, padx=40, fill="x")
        
        self.task_entry = ctk.CTkEntry(input_frame, placeholder_text="Enter new objective...", width=300)
        self.task_entry.pack(side="left", padx=(0, 10), expand=True, fill="x")
        
        btn_add_task = ctk.CTkButton(input_frame, text="Add Task", fg_color="#0A84FF", text_color="black", hover_color="#0066CC", font=ctk.CTkFont(family="Segoe UI",weight="bold"), command=self.execute_add_task)
        btn_add_task.pack(side="left")
        
        self.task_status_label = ctk.CTkLabel(self.task_frame, text="", font=ctk.CTkFont(family="Segoe UI",size=12))
        self.task_status_label.pack(anchor="w", padx=40)
        
        self.task_scroll = ctk.CTkScrollableFrame(self.task_frame, fg_color="#1e1e1e", corner_radius=15)
        self.task_scroll.pack(pady=10, padx=40, fill="both", expand=True)

    def refresh_task_data(self):
        """Silently queries the database and rebuilds the task UI matrix."""
        for widget in self.task_scroll.winfo_children():
            widget.destroy()
            
        tasks = get_active_tasks()
        
        if not tasks:
            empty_lbl = ctk.CTkLabel(self.task_scroll, text="No objectives logged. System nominal.", text_color="#6b7280")
            empty_lbl.pack(pady=20)
        else:
            for t in tasks:
                t_id, desc, due, is_completed = t
                row = ctk.CTkFrame(self.task_scroll, fg_color="transparent")
                row.pack(fill="x", pady=5)
                
                # The Checkbox
                chk = ctk.CTkCheckBox(row, text=desc, font=ctk.CTkFont(family="Segoe UI", size=14), text_color="#a3a3a3", hover_color="#0A84FF", command=lambda id=t_id: self.execute_complete_task(id))
                if is_completed:
                    chk.select()
                chk.pack(side="left", padx=10, pady=5)
                
                # The Delete Button
                btn_del = ctk.CTkButton(row, text="X", width=30, fg_color="#333333", hover_color="#ff4444", text_color="white", command=lambda id=t_id: self.execute_delete_task(id))
                btn_del.pack(side="right", padx=(5, 10))
                
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
                self.task_entry.delete(0, 'end')
                self.refresh_task_data()
            else:
                self.task_status_label.configure(text="System Alert: Backend write failed.", text_color="red")
        
        except ValueError as e:
            self.task_status_label.configure(text=f"Validation Error: {e}", text_color="red")
            
    def execute_complete_task(self, task_id):
        """Bridge to flip the binary state to True (1) and purge from the active UI."""
        if complete_task(task_id):
            self.refresh_task_data()
            
    def execute_delete_task(self, task_id):
        """Bridge command to permanently delete a task and reboot the UI."""
        if delete_task(task_id):
            self.refresh_task_data()
        
    def execute_delete_envelope(self):
        """Summons the confirmation firewall before executing the Merge & Purge."""
        selected_env_name = self.env_var.get()
        
        if selected_env_name == "+ Add New Category...":
            return
        
        if selected_env_name == "Master Pool":
            self.status_lbl.configure(text="System Alert: The Master Pool cannot be deleted.", text_color="red")
            return
        env_id = self.env_mapping.get(selected_env_name)
        if not env_id:
            return
        
        
        warning_txt = f"Warning: You are about to permanently delete the '{selected_env_name}' category. \n\nAny remaining balance will be refunded to the Master Pool, and all past transactions will be securely archived. \n\nProceed with deletion?"
        
        dialog = CustomConfirmDialog("SYSTEM OVERRIDE", warning_txt)
        confirm = dialog.get_result()
        
        if confirm:
            if delete_custom_envelope(env_id, selected_env_name):
                self.status_lbl.configure(text=f"System OS: '{selected_env_name}' purged successfully.", text_color="#0A84FF")
                self.env_var.set("Master Pool")
                self.refresh_dashboard_data()
            else:
                self.status_lbl.configure(text="System Alert: Deletion failed.", text_color="red")
        
    def build_vault_frame(self):
        self.vault_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        # Header Area
        header = ctk.CTkFrame(self.vault_frame, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(30, 10))
        
        title = ctk.CTkLabel(header, text="Vault Balances", font=ctk.CTkFont(family="Segoe UI",size=28, weight="bold"))
        title.pack(side="left")
        
        # The Master Replenish Button
        btn_replenish = ctk.CTkButton(header, text="RUN MONTHLY REPLENISH", fg_color="#0A84FF", text_color="black", hover_color="#0066CC", font=ctk.CTkFont(family="Segoe UI",weight="bold"), command=self.trigger_monthly_cycle)
        btn_replenish.pack(side="right")
        
        self.vault_scroll = ctk.CTkScrollableFrame(self.vault_frame, fg_color="transparent")
        self.vault_scroll.pack(fill="both", expand=True, padx=30, pady=10)
        self.vault_scroll.grid_columnconfigure((0, 1), weight=1)

    def refresh_vault_data(self):
        for widget in self.vault_scroll.winfo_children():
            widget.destroy()
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT envelope_id, name, allocated_amount, current_balance FROM Envelopes ORDER BY envelope_id ASC")
        vaults = cursor.fetchall()
        conn.close()
        
        for i, (env_id, name, target, balance) in enumerate(vaults):
            row = i // 2
            col = i % 2
            
            card = ctk.CTkFrame(self.vault_scroll, fg_color="#1e1e1e", corner_radius=15)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            lbl_name = ctk.CTkLabel(card, text=name, font=ctk.CTkFont(family="Segoe UI",size=16, weight="bold"), text_color="#6b7280")
            lbl_name.pack(pady=(15, 0))
            
            if env_id != 1:
                lbl_target = ctk.CTkLabel(card, text=f"Target: ₹{target:,.2f}", font=ctk.CTkFont(family="Segoe UI",size=12), text_color="#a3a3a3")
                lbl_target.pack(pady=(0, 10))
            else:
                ctk.CTkLabel(card, text="Reservoir", font=ctk.CTkFont(family="Segoe UI",size=12), text_color="#a3a3a3").pack(pady=(0, 10))
            
            lbl_bal = ctk.CTkLabel(card, text=f"₹{balance:,.2f}", font=ctk.CTkFont(family="Segoe UI",size=32, weight="bold"), text_color="#0A84FF")
            lbl_bal.pack(pady=(0, 10))
            
            # The Edit Target Button
            if env_id != 1:
                btn_edit = ctk.CTkButton(card, text="Edit Target", width=100, height=24, fg_color="#333333", hover_color="#444444", command=lambda e=env_id, n=name: self.prompt_target_update(e, n))
                btn_edit.pack(pady=(0, 15))

    def prompt_target_update(self, env_id, env_name):
        """Spawns an OS dialog to ask the user for a new Principal Target."""
        dialog = ctk.CTkInputDialog(text=f"Enter new monthly target for {env_name}:", title="Update Target")
        result = dialog.get_input()
        
        if result is not None:
            try:
                new_target = float(result)
                if update_category_principal(env_id, new_target):
                    self.refresh_vault_data() 
            except ValueError:
                pass 

    def trigger_monthly_cycle(self):
        """Fires the Auto-Replenish engine and renders the result modal."""
        success, message = execute_monthly_replenish()
        
        title = "CYCLE COMPLETE" if success else "SYSTEM ALERT"
        dialog = CustomConfirmDialog(title, message)
        dialog.get_result()
        
        self.refresh_vault_data()
    
    def build_settings_frame(self):
        """Constructs the Settings UI and the Danger Zone."""
        self.settings_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        title = ctk.CTkLabel(self.settings_frame, text="System Preferences", font=ctk.CTkFont(family="Segoe UI",size=28, weight="bold"))
        title.pack(pady=(30, 10), anchor="w", padx=40)
        
        # --- The Danger Zone ---
        danger_zone = ctk.CTkFrame(self.settings_frame, fg_color="#2b1a1a", border_color="#ff4444", border_width=1, corner_radius=15)
        danger_zone.pack(pady=20, padx=40, fill="x")
        
        lbl_danger = ctk.CTkLabel(danger_zone, text="DANGER ZONE", font=ctk.CTkFont(family="Segoe UI",weight="bold", size=14), text_color="#ff4444")
        lbl_danger.pack(pady=(15, 5), anchor="w", padx=20)
        
        desc = ctk.CTkLabel(danger_zone, text="Permanently wipe all data, transactions, and custom categories. This cannot be undone.", text_color="#a3a3a3")
        desc.pack(anchor="w", padx=20, pady=(0, 15))
        
        btn_reset = ctk.CTkButton(danger_zone, text="FACTORY RESET APEX OS", fg_color="#ff4444", text_color="white", hover_color="#cc0000", font=ctk.CTkFont(family="Segoe UI",weight="bold"), command=self.trigger_master_reset)
        btn_reset.pack(anchor="w", padx=20, pady=(0, 20))

    def trigger_master_reset(self):
        """Deploys the Custom Modal to verify the nuclear launch."""
        warning_txt = "CRITICAL WARNING: You are initiating a Factory Reset.\n\nThis will permanently destroy your Master Pool, all Envelopes, all Task data, and your entire Transaction Tape.\n\nDo you wish to nuke the database?"
        dialog = CustomConfirmDialog("SYSTEM OVERRIDE: FACTORY RESET", warning_txt)
        confirm = dialog.get_result()
        
        if confirm:
            if execute_factory_reset():
                # Reboot the UI back to the completely empty dashboard
                self.show_dashboard()
        
    def build_telemetry_frame(self):
        self.telemetry_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        # Header with View Toggle
        header_frame = ctk.CTkFrame(self.telemetry_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=(30, 10))
        
        title = ctk.CTkLabel(header_frame, text="Telemetry Matrix", font=ctk.CTkFont(family="Segoe UI",size=28, weight="bold"))
        title.pack(side="left")
        
        # The View Switcher
        self.chart_view_var = ctk.StringVar(value="Current Month (Donut)")
        self.view_toggle = ctk.CTkSegmentedButton(
            header_frame, 
            values=["Current Month (Donut)", "Yearly Volume (Bar)"], 
            variable=self.chart_view_var, 
            command=self.refresh_telemetry_data, # Auto-refreshes when clicked
            selected_color="#0A84FF", 
            selected_hover_color="#0066CC", 
            unselected_color="#333333", 
            text_color="white"
        )
        self.view_toggle.pack(side="right")
        self.btn_export = ctk.CTkButton(header_frame, text="Export CSV Report", fg_color="#0A84FF", text_color="white", font=ctk.CTkFont(family="Segoe UI", weight="bold"), command=self.execute_export_report)
        self.btn_export.pack(side="right", padx=20)
        
        
        
        # The Dark Console Container
        self.chart_container = ctk.CTkFrame(self.telemetry_frame, fg_color="#1e1e1e", corner_radius=15)
        self.chart_container.pack(pady=20, padx=40, fill="both", expand=True)

    def refresh_telemetry_data(self, *args):
        """Renders either the Donut or the Bar graph based on the toggle state."""
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        for widget in self.chart_container.winfo_children():
            widget.destroy()
            
        current_view = self.chart_view_var.get()
        
        # Create a single, massive Matplotlib Figure
        fig, ax = plt.subplots(figsize=(8, 5), facecolor="#1e1e1e")
        ax.set_facecolor("#1e1e1e")
        colors = ['#0A84FF', '#ff4444', '#ffcc00', '#cc33ff', '#3399ff', '#ff3399']

        if "Donut" in current_view:
            # --- MONTHLY DONUT LOGIC ---
            data = get_pie_chart_data()
            ax.set_title("Current Calendar Month Burn", color="white", weight="bold", pad=20)
            
            if data:
                wedges, texts, autotexts = ax.pie(
                    list(data.values()), labels=list(data.keys()), autopct='%1.1f%%', 
                    startangle=90, pctdistance=0.75, colors=colors,
                    textprops={'color': "white", 'weight': 'bold'},
                    wedgeprops={'edgecolor': '#1e1e1e', 'linewidth': 2, 'width': 0.4} 
                )
                plt.setp(texts, size=12)
                plt.setp(autotexts, size=10, weight="bold", color="black")
                ax.axis('equal')
            else:
                ax.text(0.5, 0.5, 'No expenses logged this month.', color='white', ha='center', va='center', size=14)
                
        else:
            # --- YEARLY BAR GRAPH LOGIC ---
            data = get_bar_chart_data()
            ax.set_title("Year-to-Date Burn Rate", color="white", weight="bold", pad=20)
            
            months = list(data.keys())
            totals = list(data.values())
            
            # Matplotlib auto-scales the Y-axis based on the highest total
            bars = ax.bar(months, totals, color="#0A84FF", edgecolor="#0066CC", width=0.6)
            
            # Styling the grid
            ax.tick_params(colors='white', labelsize=10)
            for spine in ax.spines.values():
                spine.set_color('#333333')
                
            # Add dollar amounts hovering over the bars (only if > 0)
            for bar in bars:
                yval = bar.get_height()
                if yval > 0:
                    offset = max(totals) * 0.02 if max(totals) > 0 else 1
                    ax.text(bar.get_x() + bar.get_width()/2, yval + offset, f'₹{yval:,.0f}', ha='center', va='bottom', color='white', size=10, weight='bold')

        plt.tight_layout()
        
        # Render to UI
        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)
        plt.close(fig)
        
    def build_debt_frame(self):
        """Constructs the split-pane matrix for Peer-to-Peer IOUs."""
        self.debt_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        # Header
        title = ctk.CTkLabel(self.debt_frame, text="Debt Ledger", font=ctk.CTkFont(family="Segoe UI",size=28, weight="bold"))
        title.pack(pady=(30, 10), anchor="w", padx=40)
        
        # --- TOP MODULE: The IOU Control Panel ---
        form_card = ctk.CTkFrame(self.debt_frame, fg_color="#1e1e1e", corner_radius=15)
        form_card.pack(pady=10, padx=40, fill="x")
        
        form_title = ctk.CTkLabel(form_card, text="SECURE NEW IOU", font=ctk.CTkFont(family="Segoe UI",size=12, weight="bold"), text_color="#6b7280")
        form_title.pack(anchor="w", padx=20, pady=(15, 5))
        
        input_grid = ctk.CTkFrame(form_card, fg_color="transparent")
        input_grid.pack(fill="x", padx=20, pady=(0, 20))
        
        self.debt_name_entry = ctk.CTkEntry(input_grid, placeholder_text="Person's Name", width=200)
        self.debt_name_entry.pack(side="left", padx=(0, 15))
        
        self.debt_amt_entry = ctk.CTkEntry(input_grid, placeholder_text="Amount", width=120)
        self.debt_amt_entry.pack(side="left", padx=(0, 15))
        
        self.debt_type_var = ctk.StringVar(value="Lent")
        self.debt_toggle = ctk.CTkSegmentedButton(input_grid, values=["Lent", "Borrowed"], variable=self.debt_type_var, selected_color="#3399ff", selected_hover_color="#2277cc")
        self.debt_toggle.pack(side="left", padx=(0, 15))
        
        self.btn_secure_iou = ctk.CTkButton(input_grid, text="Execute Ledger Entry", fg_color="#3399ff", text_color="black", hover_color="#2277cc", font=ctk.CTkFont(family="Segoe UI",weight="bold"), command=self.execute_iou_creation)
        self.btn_secure_iou.pack(side="left", expand=True, fill="x")
        
        # --- BOTTOM MODULE: The Split-Pane Matrix ---
        ledger_container = ctk.CTkFrame(self.debt_frame, fg_color="transparent")
        ledger_container.pack(pady=10, padx=40, fill="both", expand=True)
        
        # Force a perfect 50/50 split
        ledger_container.grid_columnconfigure((0, 1), weight=1, uniform="a")
        ledger_container.grid_rowconfigure(0, weight=1)
        
        # Left Column: Assets (Money Owed to You)
        self.lent_scroll = ctk.CTkScrollableFrame(ledger_container, fg_color="#1e1e1e", corner_radius=15)
        self.lent_scroll.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        lbl_assets = ctk.CTkLabel(self.lent_scroll, text="ASSETS (Owed To You)", font=ctk.CTkFont(family="Segoe UI",size=14, weight="bold"), text_color="#0A84FF")
        lbl_assets.pack(pady=(10, 20))
        
        # Right Column: Liabilities (Money You Owe)
        self.borrowed_scroll = ctk.CTkScrollableFrame(ledger_container, fg_color="#1e1e1e", corner_radius=15)
        self.borrowed_scroll.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        lbl_liab = ctk.CTkLabel(self.borrowed_scroll, text="LIABILITIES (You Owe)", font=ctk.CTkFont(family="Segoe UI",size=14, weight="bold"), text_color="#ff4444")
        lbl_liab.pack(pady=(10, 20))
        
    def execute_iou_creation(self):
        """Validates and executes a new Peer-to-Peer debt."""
        name = self.debt_name_entry.get().strip()
        raw_amt = self.debt_amt_entry.get()
        l_type = self.debt_type_var.get()
        
        if not name or not raw_amt:
            print("System Alert: Missing name or amount.")
            return # Ignore empty submissions
            
        try:
            amt = float(raw_amt)
            if amt <= 0: raise ValueError
            
            # Formulate the payload
            loan = LoanModel(person_name=name, principal_amount=amt, loan_type=l_type, created_at=date.today())
            
            # Execute backend write
            if create_loan(loan):
                # Clear the input fields
                self.debt_name_entry.delete(0, 'end')
                self.debt_amt_entry.delete(0, 'end')
                
                # Instantly reload the UI matrix
                self.refresh_debt_data() 
                
                print(f"System OS: Successfully logged {l_type} IOU for {name}.")
                
        except ValueError:
            print("System Alert: Invalid amount entered. Must be a positive number.")
        
    def refresh_debt_data(self):
        """Pulls B-tree data and mathematically sorts IOUs into the Split-Pane matrix."""
        # 1. Purge both of the NEW split columns completely
        for widget in self.lent_scroll.winfo_children():
            widget.destroy()
                
        for widget in self.borrowed_scroll.winfo_children():
            widget.destroy()

        # 2. Re-draw the Structural Headers
        ctk.CTkLabel(self.lent_scroll, text="ASSETS (Owed To You)", font=ctk.CTkFont(family="Segoe UI",size=14, weight="bold"), text_color="#0A84FF").pack(pady=(10, 20))
        ctk.CTkLabel(self.borrowed_scroll, text="LIABILITIES (You Owe)", font=ctk.CTkFont(family="Segoe UI",size=14, weight="bold"), text_color="#ff4444").pack(pady=(10, 20))

        # 3. Fetch Active Ledger Data
        loans = get_active_loans()
        
        if not loans:
            ctk.CTkLabel(self.lent_scroll, text="No active assets.", text_color="#6b7280", font=ctk.CTkFont(family="Segoe UI",slant="italic")).pack(pady=20)
            ctk.CTkLabel(self.borrowed_scroll, text="No active liabilities.", text_color="#6b7280", font=ctk.CTkFont(family="Segoe UI",slant="italic")).pack(pady=20)
            return

        # 4. Render Cards dynamically into the correct columns
        for l_id, name, principal, balance, l_type in loans:
            # Mathematical routing based on Debt Type
            parent = self.lent_scroll if l_type == "Lent" else self.borrowed_scroll
            color = "#0A84FF" if l_type == "Lent" else "#ff4444"
            btn_text = "Log Receipt" if l_type == "Lent" else "Log Payment"
            
            # The Card Background
            card = ctk.CTkFrame(parent, fg_color="#2b2b2b", corner_radius=15)
            card.pack(fill="x", pady=5, padx=10)
            
            # Left side of card: Typography & Progress
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", padx=15, pady=15, fill="x", expand=True)
            
            ctk.CTkLabel(info_frame, text=name, font=ctk.CTkFont(family="Segoe UI",weight="bold", size=14), text_color="white").pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"₹{balance:,.2f} remaining of ₹{principal:,.2f}", font=ctk.CTkFont(family="Segoe UI",size=12), text_color="#a3a3a3").pack(anchor="w")
            
            # Right side of card: Execution Bridge
            btn_repay = ctk.CTkButton(card, text=btn_text, width=100, fg_color="transparent", border_width=1, border_color=color, text_color=color, hover_color="#333333", command=lambda id=l_id, n=name, bal=balance: self.trigger_repayment(id, n, bal))
            btn_repay.pack(side="right", padx=15)

    # --- EXECUTION BRIDGES ---
    def trigger_repayment(self, loan_id, name, current_balance):
        dialog = ctk.CTkInputDialog(text=f"Enter payment amount for {name} (Max: ₹{current_balance:,.2f}):", title="Process Repayment")
        result = dialog.get_input()
        
        if result:
            try:
                amt = float(result)
                repay_payload = LoanRepaymentModel(loan_id=loan_id, amount=amt)
                if repay_loan(repay_payload):
                    self.refresh_debt_data()
            except ValueError:
                pass
    
    def execute_export_report(self):
        """Bridge to generate the CSV report."""
        filepath = generate_transaction_ledger()
        if filepath:
            # Temporarily changes the app window title to show success!
            self.title(f"Apex Finance OS - Report Successfully Saved to: {filepath}")

if __name__ == "__main__":
    # The First Boot Protocol
    if not DB_PATH.exists():
        print("System OS: First boot detected. Building matrix architecture...")
        initialize_database()
        seed_default_categories()
        
    app = ApexFinanceApp()
    app.mainloop()