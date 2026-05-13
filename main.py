import customtkinter as ctk
import sqlite3
import matplotlib.pyplot as plt
from datetime import date
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from backend_db import DB_PATH, save_transaction, distribute_income, get_recent_transactions, delete_transaction, create_task, complete_task, get_active_tasks, add_custom_envelope, delete_custom_envelope, execute_factory_reset, add_income_to_master, update_category_principal, execute_monthly_replenish, get_pie_chart_data, get_bar_chart_data, get_active_loans, create_loan, repay_loan, seed_default_categories, delete_task, export_data_to_csv, reset_database_registry
from database_setup import initialize_database
from data_models import TransactionModel, IncomeAllocationModel, TaskModel, LoanRepaymentModel, LoanModel
from report_generation import generate_transaction_ledger
from analytical_engine import run_predictive_engine
import re

# UI Config
ctk.set_default_color_theme("blue")
# UI Design System: Fintech Luxury
ctk.set_appearance_mode("Dark")

# Protocol: Defining Global Brand Colors
BRAND_ACCENT = "#1E90FF"  # Deep Royal Slate (More muted/expensive feel)
BG_MAIN = "#080808"       # Near Black (Pure Onyx)
CARD_BG = "#121212"       # Subtle Elevation
TEXT_MUTED = "#606060"    # Darkened Steel

class CustomConfirmDialog(ctk.CTkToplevel):
    """A high-contrast luxury modal with expanded geometry to prevent clipping."""
    def __init__(self, title, message):
        super().__init__()
        self.title("System Decision")
        
        # PROTOCOL 1: Geometry Expansion
        # Increased height from 280 to 340 to accommodate multi-line warnings
        self.geometry("450x340") 
        self.resizable(False, False)
        self.configure(fg_color="#080808")
        self.attributes("-topmost", True)
        
        self.result = False
        
        # 1. Critical Accent Banner
        ctk.CTkFrame(self, fg_color="#ff4444", height=4, corner_radius=0).pack(fill="x", side="top")
        
        # 2. Typography Hierarchy
        lbl_title = ctk.CTkLabel(self, text=title.upper(), 
                                 font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), 
                                 text_color="#ff4444")
        lbl_title.pack(pady=(25, 5))
        
        lbl_msg = ctk.CTkLabel(self, text=message, 
                               font=ctk.CTkFont(family="Segoe UI", size=15), 
                               text_color="white", wraplength=380)
        lbl_msg.pack(pady=(10, 20), padx=30)
        
        # PROTOCOL 2: Absolute Packing 
        # Removed 'side="bottom"' to let the frame flow naturally under the text
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=40, pady=(10, 25))
        
        btn_cancel = ctk.CTkButton(btn_frame, text="ABORT", height=45,
                                   fg_color="#1a1a1a", hover_color="#252525", 
                                   text_color="white", font=ctk.CTkFont(family="Segoe UI", weight="bold"),
                                   command=self.cancel_action)
        btn_cancel.pack(side="left", expand=True, padx=(0, 10))
        
        btn_confirm = ctk.CTkButton(btn_frame, text="PROCEED", height=45,
                                    fg_color="#ff4444", hover_color="#cc0000", 
                                    text_color="black", font=ctk.CTkFont(family="Segoe UI", weight="bold"), 
                                    command=self.confirm_action)
        btn_confirm.pack(side="right", expand=True, padx=(10, 0))
        
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
        """Halts the main Python thread until a button is clicked."""
        self.wait_window()
        return self.result

class AddIncomeDialog(ctk.CTkToplevel):
    """A dedicated luxury portal for Master Pool fund injections."""
    def __init__(self):
        super().__init__()
        self.title("Registry Update")
        self.geometry("400x380")
        self.resizable(False, False)
        self.configure(fg_color="#080808")
        self.attributes("-topmost", True)
        
        self.amount = None
        self.note = None
        
        # 1. Luxury Accent Banner (Blue for Ingestion)
        ctk.CTkFrame(self, fg_color=BRAND_ACCENT, height=4, corner_radius=0).pack(fill="x", side="top")
        
        # 2. Header
        lbl = ctk.CTkLabel(self, text="FUND INJECTION", 
                           font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), 
                           text_color=BRAND_ACCENT)
        lbl.pack(pady=(30, 0))
        
        ctk.CTkLabel(self, text="Master Pool", 
                     font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"), 
                     text_color="white").pack(pady=(0, 20))
        
        # 3. Form Matrix (Obsidian Entry Protocol)
        self.amt_entry = ctk.CTkEntry(self, placeholder_text="Amount (e.g. 1500)", 
                                      width=320, height=50, fg_color="#121212", 
                                      border_width=0, corner_radius=12)
        self.amt_entry.pack(pady=10)
        
        self.note_entry = ctk.CTkEntry(self, placeholder_text="Source / Description", 
                                       width=320, height=50, fg_color="#121212", 
                                       border_width=0, corner_radius=12)
        self.note_entry.pack(pady=10)
        
        # 4. Action Button
        btn = ctk.CTkButton(self, text="AUTHORIZE DEPOSIT", height=55,
                            fg_color="white", text_color="black", 
                            hover_color="#e0e0e0", font=ctk.CTkFont(family="Segoe UI", weight="bold"), 
                            command=self.submit)
        btn.pack(pady=30, padx=40, fill="x")
        
        self.wait_visibility()
        self.grab_set()
        self.focus_force()

    def submit(self):
        self.amount = self.amt_entry.get()
        self.note = self.note_entry.get()
        self.destroy()

    def get_input(self): self.wait_window(); return self.amount, self.note

class ForecastDialog(ctk.CTkToplevel):
    """A sleek, consumer-facing alert modal for predictive heuristics."""
    def __init__(self, report_text):
        super().__init__()
        self.title("Budget Alert")
        self.geometry("450x470")
        self.resizable(False, False)
        self.configure(fg_color="#111111")
        self.attributes("-topmost", True)

        # 1. Threat Detection & Theming
        if "STATUS BLACK" in report_text or "STATUS RED" in report_text:
            self.theme_color = "#ff4444" 
            self.bg_color = "#2b1a1a"
            self.icon = "⚠️ CRITICAL ALERT"
        elif "STATUS YELLOW" in report_text:
            self.theme_color = "#ffcc00"
            self.bg_color = "#2b261a"
            self.icon = "⚠️ SPENDING WARNING"
        else:
            self.theme_color = "#00ffcc"
            self.bg_color = "#1a2b26"
            self.icon = "✅ TRAJECTORY SECURE"

        # 2. Data Parsing Engine (Regex extraction)
        env_match = re.search(r"\[(.*?)\]", report_text)
        reserve_match = re.search(r"Current Reserve: (₹[\d,.]+)", report_text)
        velocity_match = re.search(r"Burning (₹[\d,.]+)", report_text)
        eom_match = re.search(r"Projected EOM Balance: (₹[-,\d.]+)", report_text)
        status_match = re.search(r">> (.*) <<", report_text)

        env_name = env_match.group(1).title() if env_match else "Category"
        reserve = reserve_match.group(1) if reserve_match else "N/A"
        velocity = velocity_match.group(1) if velocity_match else "N/A"
        eom = eom_match.group(1) if eom_match else "N/A"
        status_msg = status_match.group(1).replace("STATUS RED: ", "").replace("STATUS BLACK: ", "").replace("STATUS YELLOW: ", "") if status_match else "Unknown trajectory."

        # 3. Modern UI Architecture
        # Top Banner
        banner = ctk.CTkFrame(self, fg_color=self.theme_color, corner_radius=0, height=8)
        banner.pack(fill="x", side="top")

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(25, 10))
        
        ctk.CTkLabel(header_frame, text=self.icon, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=self.theme_color).pack(anchor="w")
        ctk.CTkLabel(header_frame, text=f"{env_name} Outlook", font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"), text_color="white").pack(anchor="w")

        # Status Message Bubble
        msg_frame = ctk.CTkFrame(self, fg_color=self.bg_color, corner_radius=10)
        msg_frame.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(msg_frame, text=status_msg, font=ctk.CTkFont(family="Segoe UI", size=13), text_color="white", wraplength=350, justify="left").pack(padx=15, pady=15, anchor="w")

        # Metrics Grid (2x2)
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(fill="x", padx=30, pady=10)
        grid_frame.grid_columnconfigure((0, 1), weight=1)

        # Card 1: Current Reserve
        card1 = ctk.CTkFrame(grid_frame, fg_color="#1e1e1e", corner_radius=10)
        card1.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="nsew")
        ctk.CTkLabel(card1, text="Current Reserve", font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#a3a3a3").pack(anchor="w", padx=15, pady=(15, 0))
        ctk.CTkLabel(card1, text=reserve, font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color="white").pack(anchor="w", padx=15, pady=(0, 15))

        # Card 2: Burn Rate
        card2 = ctk.CTkFrame(grid_frame, fg_color="#1e1e1e", corner_radius=10)
        card2.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="nsew")
        ctk.CTkLabel(card2, text="Daily Burn Rate", font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#a3a3a3").pack(anchor="w", padx=15, pady=(15, 0))
        ctk.CTkLabel(card2, text=f"{velocity}/day", font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color="white").pack(anchor="w", padx=15, pady=(0, 15))

        # Card 3: Projected EOM (Spans both columns)
        card3 = ctk.CTkFrame(grid_frame, fg_color="#1e1e1e", corner_radius=10)
        card3.grid(row=1, column=0, columnspan=2, pady=5, sticky="nsew")
        ctk.CTkLabel(card3, text="Projected End-of-Month Balance", font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#a3a3a3").pack(anchor="w", padx=15, pady=(15, 0))
        ctk.CTkLabel(card3, text=eom, font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"), text_color=self.theme_color).pack(anchor="w", padx=15, pady=(0, 15))

        # Action Button
        btn = ctk.CTkButton(self, text="Got It", height=10, fg_color="#333333", hover_color="#444444", text_color="white", font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"), command=self.destroy)
        btn.pack(fill="x", padx=30, pady=(15, 20), ipady=10)

        self.wait_visibility()
        self.grab_set()
        self.focus_force()
        self.wait_window()

class SystemMessageDialog(ctk.CTkToplevel):
    """A luxury-themed universal feedback modal for errors, warnings, and alerts."""
    def __init__(self, title, message, color="#0A84FF"):
        super().__init__()
        self.title("System Notification")
        self.geometry("400x260")
        self.resizable(False, False)
        self.configure(fg_color="#080808")
        self.attributes("-topmost", True)

        ctk.CTkFrame(self, fg_color=color, height=4, corner_radius=0).pack(fill="x", side="top")
        ctk.CTkLabel(self, text=title.upper(), font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color=color).pack(pady=(25, 5))
        ctk.CTkLabel(self, text=message, font=ctk.CTkFont(family="Segoe UI", size=15), text_color="white", wraplength=320).pack(pady=10, padx=20)

        btn = ctk.CTkButton(self, text="ACKNOWLEDGE", height=45, fg_color="#1a1a1a", hover_color="#252525", text_color="white", font=ctk.CTkFont(family="Segoe UI", weight="bold"), command=self.destroy)
        btn.pack(side="bottom", pady=25, padx=40, fill="x")

        self.wait_visibility()
        self.grab_set()
        self.focus_force()

class LuxuryInputDialog(ctk.CTkToplevel):
    """A sleek, high-contrast modal designed specifically for capturing user input."""
    def __init__(self, title, prompt, on_submit):
        super().__init__()
        self.title("System Request")
        self.geometry("400x280")
        self.resizable(False, False)
        self.configure(fg_color="#080808")
        self.attributes("-topmost", True)
        
        # Callback function to execute when the user submits
        self.on_submit = on_submit

        # Luxury Accent Banner
        ctk.CTkFrame(self, fg_color=BRAND_ACCENT, height=4, corner_radius=0).pack(fill="x", side="top")

        # Typography
        ctk.CTkLabel(self, text=title.upper(), 
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), 
                     text_color=BRAND_ACCENT).pack(pady=(25, 5))
                     
        ctk.CTkLabel(self, text=prompt, 
                     font=ctk.CTkFont(family="Segoe UI", size=13), 
                     text_color="white").pack(pady=(0, 15))

        # Obsidian Entry Protocol
        self.entry = ctk.CTkEntry(self, placeholder_text="Enter value...", 
                                  height=45, fg_color="#121212", border_width=0, corner_radius=10)
        self.entry.pack(fill="x", padx=40, pady=10)
        
        # Focus the entry field automatically so you can start typing immediately
        self.entry.focus()

        # Action Button
        btn = ctk.CTkButton(self, text="SUBMIT UPDATE", height=45, 
                            fg_color=BRAND_ACCENT, hover_color="#0066CC", text_color="black", 
                            font=ctk.CTkFont(family="Segoe UI", weight="bold"), 
                            command=self.submit)
        btn.pack(fill="x", padx=40, pady=20)

        # OS Thread Hijack
        self.wait_visibility()
        self.grab_set()

    def submit(self):
        """Captures the input, triggers the callback, and destroys the modal."""
        val = self.entry.get().strip()
        if val:
            self.on_submit(val)
            self.destroy()

class ApexFinanceApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # System State Matrix: Tracking if a screen needs a rebuild
        self.needs_refresh = {
            "dashboard": True,
            "vaults": True,
            "tasks": True,
            "telemetry": True,
            "debt": True
        }
        
        # Window
        self.title("Apex Finance OS")
        self.geometry("1000x600")
        self.minsize(800, 500)
        
        # The Grid Matrix
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # The Sidebar Container
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#111111", border_width=0)
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
        self.configure(fg_color=BG_MAIN)
        self.main_container = ctk.CTkFrame(self, corner_radius=20, fg_color=BG_MAIN, border_width=0)
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
        if self.needs_refresh["debt"]:
            self.refresh_debt_data()
            self.needs_refresh["debt"] = False

    def show_telemetry(self):
        self.hide_all_frames()
        self.telemetry_frame.grid(row=0, column=0, sticky="nsew")
        if self.needs_refresh["telemetry"]:
            self.refresh_telemetry_data()
            self.needs_refresh["telemetry"] = False

    def show_dashboard(self):
        self.hide_all_frames()
        self.dashboard_frame.grid(row=0, column=0, sticky="nsew")
        if self.needs_refresh["dashboard"]:
            self.refresh_dashboard_data()
            self.needs_refresh["dashboard"] = False
        
    def show_tasks(self):
        self.hide_all_frames()
        self.task_frame.grid(row=0, column=0, sticky="nsew")
        self.refresh_task_data()

    def show_vaults(self):
        self.hide_all_frames()
        self.vault_frame.grid(row=0, column=0, sticky="nsew")
        if self.needs_refresh["vaults"]:
            self.refresh_vault_data()
            self.needs_refresh["vaults"] = False

    def show_settings(self):
        self.hide_all_frames()
        self.settings_frame.grid(row=0, column=0, sticky="nsew")

    def build_dashboard_frame(self):
        """Refactors the Dashboard into a high-contrast Luxury Matrix."""
        # Protocol: Resetting the frame with a deep onyx background
        self.dashboard_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.dashboard_frame.grid(row=0, column=0, sticky="nsew")

        # --- SECTION 1: THE HERO HEADER ---
        header_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=(30, 10))
        
        ctk.CTkLabel(header_frame, text="COMMAND CENTER", 
                    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), 
                    text_color=TEXT_MUTED).pack(anchor="w")
        
        title_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_row.pack(fill="x")
        
        ctk.CTkLabel(title_row, text="Overview", 
                    font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"), 
                    text_color="white").pack(side="left")
        
        btn_income = ctk.CTkButton(title_row, text="+ DEPOSIT FUNDS", 
                                fg_color=BRAND_ACCENT, text_color="black", 
                                hover_color="#0066CC", height=40,
                                font=ctk.CTkFont(family="Segoe UI", weight="bold"), 
                                command=self.trigger_income_injection)
        btn_income.pack(side="right")
        
        # --- SECTION 2: THE RESERVOIR CARD (The "Luxury" Hero) ---
        self.hero_card = ctk.CTkFrame(self.dashboard_frame, fg_color=CARD_BG, corner_radius=20)
        self.hero_card.pack(pady=10, padx=40, fill="x")
        
        # The Accent Banner Protocol
        ctk.CTkFrame(self.hero_card, fg_color=BRAND_ACCENT, height=4, corner_radius=0).pack(fill="x", side="top")

        lbl_pool = ctk.CTkLabel(self.hero_card, text="MASTER POOL RESERVOIR", 
                                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), 
                                text_color=TEXT_MUTED)
        lbl_pool.pack(pady=(25, 0), padx=30, anchor="w")
        
        self.lbl_balance = ctk.CTkLabel(self.hero_card, text="₹0.00", 
                                        font=ctk.CTkFont(family="Segoe UI", size=64, weight="bold"), 
                                        text_color="white")
        self.lbl_balance.pack(pady=(0, 25), padx=30, anchor="w")
        
        # --- SECTION 3: TRANSACTION MODULE (The Ingestion Card) ---
        self.action_card = ctk.CTkFrame(self.dashboard_frame, fg_color=CARD_BG, corner_radius=20)
        self.action_card.pack(pady=10, padx=40, fill="x")
        
        ctk.CTkLabel(self.action_card, text="LOG NEW EXPENSE", 
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), 
                    text_color=TEXT_MUTED).pack(anchor="w", padx=30, pady=(20, 0))

        input_grid = ctk.CTkFrame(self.action_card, fg_color="transparent")
        input_grid.pack(pady=(10, 25), padx=30, fill="x")
        
        # Styled Entries
        self.amount_entry = ctk.CTkEntry(input_grid, placeholder_text="Amount", 
                                        width=120, height=45, fg_color="#252525", 
                                        border_width=0, corner_radius=10)
        self.amount_entry.pack(side="left", padx=(0, 10))
        
        self.note_entry = ctk.CTkEntry(input_grid, placeholder_text="Description", 
                                    height=45, fg_color="#252525", 
                                    border_width=0, corner_radius=10)
        self.note_entry.pack(side="left", padx=(0, 10), expand=True, fill="x")
        
        # OptionMenu styled to match the dark aesthetic
        # OptionMenu styled to match the dark aesthetic
        self.env_var = ctk.StringVar(value="Select Category")
        self.dropdown = ctk.CTkOptionMenu(
            input_grid, variable=self.env_var, values=["Loading..."], 
            height=45, fg_color="#252525", button_color="#333333",
            button_hover_color="#444444", corner_radius=10,
            command=self.handle_dropdown_selection)
        self.dropdown.pack(side="left", padx=(0, 10), expand=True, fill="x")
        
        # --- RESTORED: Category Deletion Protocol ---
        self.btn_del_env = ctk.CTkButton(input_grid, text="✕", width=45, height=45, 
                                        fg_color="#252525", hover_color="#ff4444", 
                                        text_color="white", corner_radius=10,
                                        command=self.execute_delete_envelope)
        self.btn_del_env.pack(side="left", padx=(0, 10))
        
        self.btn_submit = ctk.CTkButton(input_grid, text="Execute", 
                                        fg_color="white", text_color="black", 
                                        hover_color="#e0e0e0", height=45,
                                        font=ctk.CTkFont(family="Segoe UI", weight="bold"), 
                                        command=self.process_transaction)
        self.btn_submit.pack(side="left")

        self.status_lbl = ctk.CTkLabel(self.action_card, text="", 
                                   font=ctk.CTkFont(family="Segoe UI", size=12),
                                   text_color=BRAND_ACCENT)
        self.status_lbl.pack(anchor="w", padx=30, pady=(0, 15))
        
        # --- SECTION 4: THE TRANSACTION TAPE (The History Card) ---
        self.ledger_card = ctk.CTkFrame(self.dashboard_frame, fg_color=CARD_BG, corner_radius=20)
        self.ledger_card.pack(pady=(10, 20), padx=40, fill="both", expand=True)
        
        ctk.CTkLabel(self.ledger_card, text="LIVE TRANSACTION TAPE", 
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), 
                    text_color=TEXT_MUTED).pack(anchor="w", padx=30, pady=(20, 10))
        
        self.ledger_frame = ctk.CTkScrollableFrame(self.ledger_card, fg_color="transparent", height=200)
        self.ledger_frame.pack(pady=(0, 20), padx=20, fill="both", expand=True)

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
        """Silently queries the database and updates the UI matrix without flickering."""
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

        # Update Core Hero Text
        self.lbl_balance.configure(text=f"₹{master_balance:,.2f}")
        
        # Update Dropdown
        self.dropdown.configure(values=env_names)
        if self.env_var.get() not in env_names:
            self.env_var.set(env_names[0])

        # PROTOCOL: Eliminate Flicker by unmapping the frame during the rebuild
        # We use pack_forget instead of withdraw
        self.ledger_frame.pack_forget()

        for widget in self.ledger_frame.winfo_children():
            widget.destroy()

        transactions = get_recent_transactions()
        if not transactions:
            ctk.CTkLabel(self.ledger_frame, text="No transactions logged yet.", text_color="gray").pack(pady=20)
        else:
            for tx in transactions:
                tx_id, tx_date, env_name, amount, note = tx
                is_income = note.startswith("INCOME:") or note.startswith("CSV INCOME:")
                amt_color = BRAND_ACCENT if is_income else "#ff4444"
                prefix = "+" if is_income else "-"

                row = ctk.CTkFrame(self.ledger_frame, fg_color="transparent")
                row.pack(fill="x", pady=5)

                ctk.CTkLabel(row, text=tx_date, width=90, anchor="w", text_color="#a3a3a3").pack(side="left", padx=(10, 5))
                ctk.CTkLabel(row, text=env_name, width=120, anchor="w", font=ctk.CTkFont(family="Segoe UI",weight="bold")).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=f"{prefix}₹{amount:,.2f}", width=90, anchor="e", text_color=amt_color, font=ctk.CTkFont(family="Segoe UI",weight="bold")).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=note, width=200, anchor="w", text_color="#6b7280").pack(side="left", padx=10, expand=True, fill="x")
                ctk.CTkButton(row, text="X", width=30, fg_color="#181818", hover_color="#ff4444", text_color="white", command=lambda t_id=tx_id: self.execute_delete(t_id)).pack(side="right", padx=(5, 10))

        # Re-map the frame to the UI with original luxury constraints
        self.ledger_frame.pack(pady=(0, 20), padx=20, fill="both", expand=True)

    def process_transaction(self):
        """Dedicated execution bridge for logging expenses with threaded trajectory checks."""
        raw_amt = self.amount_entry.get()
        note_txt = self.note_entry.get()
        selected_env_name = self.env_var.get()
        
        if not raw_amt or selected_env_name in ["Select Category", "+ Add New Category...", "Loading..."]:
            SystemMessageDialog("Input Error", "Missing parameters. You must provide an amount and select a valid category.", "#ff4444")
            return
            
        try:
            amt_float = float(raw_amt)
            env_id = self.env_mapping[selected_env_name]
            
            tx = TransactionModel(
                envelope_id=env_id,
                amount=amt_float,
                transaction_date=date.today(),
                note=note_txt
            )
            
            if save_transaction(tx):
                self.amount_entry.delete(0, 'end')
                self.note_entry.delete(0, 'end')
                self.status_lbl.configure(text="Transaction Secured.", text_color=BRAND_ACCENT)
                
                # Update UI
                self.refresh_dashboard_data()
                
                # PROTOCOL: Parallel Threading to prevent UI Lag
                # We move the heavy Pandas math to a background thread
                import threading
                threading.Thread(target=self.run_background_check, args=(env_id,), daemon=True).start()
                    
            else:
                self.status_lbl.configure(text="System Alert: Backend write failed.", text_color="red")
        except ValueError:
            self.status_lbl.configure(text="System Alert: Invalid amount.", text_color="red")

    def run_background_check(self, env_id):
        """Background worker that calculates trajectory without freezing the UI."""
        report = run_predictive_engine(env_id)
        if "STATUS RED" in report or "STATUS BLACK" in report:
            # Safely hand the pop-up back to the main UI thread
            self.after(0, lambda: ForecastDialog(report))
    
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
        """Constructs the Split-Pane Task Matrix."""
        self.task_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        # --- HEADER ---
        header = ctk.CTkFrame(self.task_frame, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(30, 10))
        
        ctk.CTkLabel(header, text="OBJECTIVE REGISTRY", 
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), 
                     text_color=TEXT_MUTED).pack(anchor="w")
        
        ctk.CTkLabel(header, text="Task Tracker", 
                     font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"), 
                     text_color="white").pack(anchor="w")
        
        # --- INPUT CARD ---
        input_card = ctk.CTkFrame(self.task_frame, fg_color=CARD_BG, corner_radius=15)
        input_card.pack(pady=10, padx=40, fill="x")
        
        ctk.CTkFrame(input_card, fg_color=BRAND_ACCENT, height=3, corner_radius=0).pack(fill="x", side="top")

        self.task_entry = ctk.CTkEntry(input_card, placeholder_text="Define new financial objective...", 
                                       height=45, fg_color="#111111", border_width=0, corner_radius=10)
        self.task_entry.pack(side="left", padx=20, pady=20, expand=True, fill="x")
        
        btn_add = ctk.CTkButton(input_card, text="ADD TASK", fg_color="white", text_color="black", 
                                 width=120, height=45, font=ctk.CTkFont(family="Segoe UI", weight="bold"),
                                 hover_color="#e0e0e0", corner_radius=10,
                                 command=self.execute_add_task)
        btn_add.pack(side="right", padx=20)

        # --- SPLIT SCROLL CONTAINER ---
        scroll_container = ctk.CTkFrame(self.task_frame, fg_color="transparent")
        scroll_container.pack(fill="both", expand=True, padx=40, pady=10)
        scroll_container.grid_columnconfigure((0, 1), weight=1, uniform="task_split")

        # Left Column: Active
        active_container = ctk.CTkFrame(scroll_container, fg_color="transparent")
        active_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(active_container, text="ACTIVE", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=BRAND_ACCENT).pack(anchor="w", padx=10)
        
        self.active_task_scroll = ctk.CTkScrollableFrame(active_container, fg_color="transparent")
        self.active_task_scroll.pack(fill="both", expand=True)

        # Right Column: Completed
        completed_container = ctk.CTkFrame(scroll_container, fg_color="transparent")
        completed_container.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ctk.CTkLabel(completed_container, text="COMPLETED", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color="#00ffcc").pack(anchor="w", padx=10)
        
        self.completed_task_scroll = ctk.CTkScrollableFrame(completed_container, fg_color="transparent")
        self.completed_task_scroll.pack(fill="both", expand=True)

        self.task_status_label = ctk.CTkLabel(self.task_frame, text="", 
                                          font=ctk.CTkFont(family="Segoe UI", size=12))
        self.task_status_label.pack(anchor="w", padx=40, pady=5)

    def refresh_task_data(self):
        """Sorts tasks with a flicker-free rendering protocol."""
        # 1. UNMAP: Take the frames out of the visual matrix
        self.active_task_scroll.pack_forget()
        self.completed_task_scroll.pack_forget()

        # 2. PURGE: Wipe the old memory state
        for widget in self.active_task_scroll.winfo_children(): widget.destroy()
        for widget in self.completed_task_scroll.winfo_children(): widget.destroy()
            
        tasks = get_active_tasks()
        
        # 3. REBUILD: Reconstruct the rows in memory (invisible to user)
        for t_id, desc, due, is_completed in tasks:
            target_scroll = self.completed_task_scroll if is_completed else self.active_task_scroll
            text_color = TEXT_MUTED if is_completed else "white"

            row = ctk.CTkFrame(target_scroll, fg_color=CARD_BG, corner_radius=12)
            row.pack(fill="x", pady=6, padx=10)

            chk = ctk.CTkCheckBox(row, text=desc, font=ctk.CTkFont(family="Segoe UI", size=13), 
                                text_color=text_color, hover_color=BRAND_ACCENT,
                                command=lambda id=t_id: self.execute_complete_task(id))
            if is_completed: chk.select()
            chk.pack(side="left", padx=15, pady=12, expand=True, fill="x")

            btn_del = ctk.CTkButton(row, text="✕", width=32, height=32, 
                                    fg_color="transparent", text_color="#ff4444", 
                                    hover_color="#331a1a", corner_radius=8,
                                    command=lambda id=t_id: self.execute_delete_task(id))
            btn_del.pack(side="right", padx=10)

        # 4. REMAP: Flash the completed layout onto the screen instantly
        self.active_task_scroll.pack(fill="both", expand=True)
        self.completed_task_scroll.pack(fill="both", expand=True)
                
# --- Task Tracker Execution Bridges ---

    def execute_add_task(self):
        """Bridge to translate UI text and inject a new task into the B-tree once."""
        desc = self.task_entry.get().strip()
        
        if not desc:
            SystemMessageDialog("Registry Error", "Task description is missing. Registry cannot index an empty objective.", "#ff4444")
            return
        
        try:
            new_task = TaskModel(description=desc)
            
            # PROTOCOL: Only one execution point to prevent duplicates
            if create_task(new_task):
                self.task_entry.delete(0, 'end')
                
                # Trigger OS-wide refresh (The Dirty Flag Protocol)
                self.needs_refresh = {k: True for k in self.needs_refresh}
                
                # Execute immediate local refresh
                self.refresh_task_data()
                self.needs_refresh["tasks"] = False 
            else:
                print("System Alert: Backend write failed.")
                
        except ValueError as e:
            print(f"Validation Error: {e}")
            
    def execute_complete_task(self, task_id):
        """Toggles the completion status and re-routes the task across the split-pane."""
        if complete_task(task_id):
            # 1. Set the Dirty Flag for all other screens (Dashboard, etc.)
            self.needs_refresh = {k: True for k in self.needs_refresh}
            
            # 2. Execute the local refresh immediately
            self.refresh_task_data()
            
            # 3. Mark this screen as 'clean' since we just rebuilt it
            self.needs_refresh["tasks"] = False
        else:
            print(f"System Alert: Failed to toggle Task ID {task_id}")
                
    def execute_delete_task(self, task_id):
        if delete_task(task_id):
            self.needs_refresh = {k: True for k in self.needs_refresh}
            self.refresh_task_data()
            self.needs_refresh["tasks"] = False
        
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
        
        # Header
        header = ctk.CTkFrame(self.vault_frame, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(30, 10))
        
        ctk.CTkLabel(header, text="FINANCIAL RESERVES", 
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), 
                     text_color=TEXT_MUTED).pack(anchor="w")
        
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")
        
        ctk.CTkLabel(title_row, text="Vault Balances", 
                     font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"), 
                     text_color="white").pack(side="left")
        
        btn_replenish = ctk.CTkButton(title_row, text="RUN REPLENISH CYCLE", 
                                      fg_color=BRAND_ACCENT, text_color="black", 
                                      hover_color="#0066CC", height=40,
                                      font=ctk.CTkFont(family="Segoe UI", weight="bold"), 
                                      command=self.trigger_monthly_cycle)
        btn_replenish.pack(side="right")
        
        self.vault_scroll = ctk.CTkScrollableFrame(self.vault_frame, fg_color="transparent")
        self.vault_scroll.pack(fill="both", expand=True, padx=30, pady=10)
        self.vault_scroll.grid_columnconfigure((0, 1), weight=1)

    def refresh_vault_data(self):
        """Rebuilds the Vault Matrix with strict Null-Type sanitization."""
        
        # 1. Clear existing memory safely (without unmapping the parent frame)
        for widget in self.vault_scroll.winfo_children():
            widget.destroy()
            
        # 2. Query the Registry
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT envelope_id, name, allocated_amount, current_balance FROM Envelopes")
        vaults = cursor.fetchall()
        conn.close()
        
        # 3. Rebuild the Matrix
        for i, (env_id, name, target, balance) in enumerate(vaults):
            
            # --- CRITICAL SAFETY PROTOCOL: Data Sanitization ---
            # If the database returns NULL, force it to behave as 0.0 to prevent formatting crashes
            target = float(target) if target is not None else 0.0
            balance = float(balance) if balance is not None else 0.0
            
            row = i // 2
            col = i % 2
            
            card = ctk.CTkFrame(self.vault_scroll, fg_color=CARD_BG, corner_radius=20, height=180)
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
            card.pack_propagate(False) 

            # Luxury Accent
            ctk.CTkFrame(card, fg_color=BRAND_ACCENT if env_id != 1 else "#cc33ff", 
                         height=3, corner_radius=0).pack(fill="x", side="top")
            
            lbl_name = ctk.CTkLabel(card, text=name.upper(), 
                                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), 
                                    text_color=TEXT_MUTED)
            lbl_name.pack(pady=(15, 0), padx=20, anchor="w")
            
            lbl_bal = ctk.CTkLabel(card, text=f"₹{balance:,.2f}", 
                                    font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"), 
                                    text_color="white")
            lbl_bal.pack(pady=(2, 5), padx=20, anchor="w")
            
            target_text = f"Target: ₹{target:,.0f}" if env_id != 1 else "Master Reservoir"
            ctk.CTkLabel(card, text=target_text, text_color=TEXT_MUTED,
                         font=ctk.CTkFont(family="Segoe UI", size=12)).pack(padx=20, anchor="w")

            # Action Bar
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(side="bottom", fill="x", padx=20, pady=15)
            
            if env_id != 1:
                btn_f = ctk.CTkButton(btn_frame, text="Forecast", width=80, height=28,
                                      fg_color="#252525", hover_color="#333333",
                                      font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                                      command=lambda e=env_id: self.trigger_predictive_engine(e))
                btn_f.pack(side="right")
                
                btn_edit = ctk.CTkButton(btn_frame, text="Edit", width=60, height=28,
                                         fg_color="transparent", hover_color="#1a1a1a", 
                                         border_width=1, border_color="#333333", text_color="white",
                                         font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                                         command=lambda e=env_id, n=name: self.trigger_edit_vault(e, n))
                btn_edit.pack(side="right", padx=(0, 10))

    def trigger_edit_vault(self, env_id, env_name):
        """Execution bridge to dynamically modify Vault allocation limits."""
        
        def submit_new_limit(new_val):
            try:
                # 1. Input Validation
                new_limit = float(new_val)
                if new_limit < 0: raise ValueError
                
                # 2. Database Execution
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("UPDATE Envelopes SET allocated_amount = ? WHERE envelope_id = ?", (new_limit, env_id))
                conn.commit()
                conn.close()

                # 3. Dirty Flag UI Refresh
                self.needs_refresh = {k: True for k in self.needs_refresh}
                self.refresh_vault_data()
                SystemMessageDialog("Registry Updated", f"Allocation limit for '{env_name}' adjusted to ₹{new_limit:,.2f}.", BRAND_ACCENT)
                
            except ValueError:
                SystemMessageDialog("Input Error", "Please enter a valid positive numerical amount.", "#ff4444")

        # Deploy the Luxury Input Modal
        LuxuryInputDialog("ADJUST LIMIT", f"Enter new financial target for {env_name}:", submit_new_limit)

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

    def trigger_predictive_engine(self, env_id):
        """Bridge command that queries the Pandas engine and spawns the terminal modal."""
        report = run_predictive_engine(env_id)
        ForecastDialog(report)

    def trigger_monthly_cycle(self):
        """Fires the Auto-Replenish engine and renders the result modal."""
        success, message = execute_monthly_replenish()
        
        title = "CYCLE COMPLETE" if success else "SYSTEM ALERT"
        dialog = CustomConfirmDialog(title, message)
        dialog.get_result()
        
        self.refresh_vault_data()
    
    def build_settings_frame(self):
        """Reconstructs the Settings tab into the Elevated Obsidian design system."""
        self.settings_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        header = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(30, 20))
        ctk.CTkLabel(header, text="SYSTEM CONFIG", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w")
        ctk.CTkLabel(header, text="Preferences", font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"), text_color="white").pack(anchor="w")

        # --- MODULE 1: Database Tools ---
        db_card = ctk.CTkFrame(self.settings_frame, fg_color=CARD_BG, corner_radius=20)
        db_card.pack(pady=10, padx=40, fill="x")
        ctk.CTkFrame(db_card, fg_color=BRAND_ACCENT, height=3, corner_radius=0).pack(fill="x", side="top")
        
        db_content = ctk.CTkFrame(db_card, fg_color="transparent")
        db_content.pack(fill="x", padx=30, pady=25)
        ctk.CTkLabel(db_content, text="Database & Sync", font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color="white").pack(anchor="w")
        
        btn_row = ctk.CTkFrame(db_content, fg_color="transparent")
        btn_row.pack(fill="x", pady=(15, 0))
        ctk.CTkButton(btn_row, text="Force Ledger Sync", height=38, fg_color="#252525", hover_color="#333333", command=self.refresh_all_data).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_row, text="Export CSV", height=38, fg_color="#252525", hover_color="#333333", command=self.export_to_csv).pack(side="left")

        # --- MODULE 2: Danger Zone ---
        danger_card = ctk.CTkFrame(self.settings_frame, fg_color=CARD_BG, corner_radius=20)
        danger_card.pack(pady=10, padx=40, fill="x")
        ctk.CTkFrame(danger_card, fg_color="#ff4444", height=3, corner_radius=0).pack(fill="x", side="top")
        
        danger_content = ctk.CTkFrame(danger_card, fg_color="transparent")
        danger_content.pack(fill="x", padx=30, pady=25)
        ctk.CTkLabel(danger_content, text="System Purge", font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color="#ff4444").pack(anchor="w")
        
        ctk.CTkButton(danger_content, text="RESET ALL DATA", fg_color="#331a1a", text_color="#ff4444", hover_color="#ff4444", command=self.trigger_system_reset).pack(pady=(15, 0), anchor="w")

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
        
        header = ctk.CTkFrame(self.telemetry_frame, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(30, 10))
        
        ctk.CTkLabel(header, text="DATA ANALYTICS", 
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), 
                     text_color=TEXT_MUTED).pack(anchor="w")
        
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")
        
        ctk.CTkLabel(title_row, text="Telemetry Matrix", 
                     font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"), 
                     text_color="white").pack(side="left")
        
        # The View Switcher (Segmented Button)
        self.chart_view_var = ctk.StringVar(value="Current Month (Donut)")
        self.view_toggle = ctk.CTkSegmentedButton(
            title_row, 
            values=["Current Month (Donut)", "Yearly Volume (Bar)"], 
            variable=self.chart_view_var, 
            command=self.refresh_telemetry_data,
            selected_color=BRAND_ACCENT, 
            unselected_color="#181818", 
            text_color="white"
        )
        self.view_toggle.pack(side="right", padx=10)

        # The Luxury Chart Card
        self.chart_card = ctk.CTkFrame(self.telemetry_frame, fg_color=CARD_BG, corner_radius=20)
        self.chart_card.pack(pady=20, padx=40, fill="both", expand=True)
        
        self.chart_container = ctk.CTkFrame(self.chart_card, fg_color="transparent")
        self.chart_container.pack(fill="both", expand=True, padx=20, pady=20)

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
        """Constructs the Luxury IOU Matrix with Pixel-Perfect Alignment."""
        self.debt_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        # --- SECTION 1: HEADER ---
        header = ctk.CTkFrame(self.debt_frame, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(30, 10))
        
        ctk.CTkLabel(header, text="PEER-TO-PEER LEDGER", 
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), 
                     text_color=TEXT_MUTED).pack(anchor="w")
        
        ctk.CTkLabel(header, text="Debt Registry", 
                     font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"), 
                     text_color="white").pack(anchor="w")
        
        # --- SECTION 2: IOU CONTROL PANEL (Input Card) ---
        form_card = ctk.CTkFrame(self.debt_frame, fg_color=CARD_BG, corner_radius=20)
        form_card.pack(pady=10, padx=40, fill="x")
        
        # Luxury Accent Banner (Matches Dashboard & Vaults)
        ctk.CTkFrame(form_card, fg_color=BRAND_ACCENT, height=3, corner_radius=0).pack(fill="x", side="top")
        
        input_grid = ctk.CTkFrame(form_card, fg_color="transparent")
        input_grid.pack(fill="x", padx=30, pady=25)
        
        # Protocol: Uniform Height Variable to lock the geometry
        UI_H = 45 

        self.debt_name_entry = ctk.CTkEntry(input_grid, placeholder_text="Person Name", 
                                            height=UI_H, fg_color="#111111", 
                                            border_width=0, corner_radius=10)
        self.debt_name_entry.pack(side="left", padx=(0, 10), expand=True, fill="x")
        
        self.debt_amt_entry = ctk.CTkEntry(input_grid, placeholder_text="Amount", 
                                           width=120, height=UI_H, fg_color="#111111", 
                                           border_width=0, corner_radius=10)
        self.debt_amt_entry.pack(side="left", padx=(0, 10))
        
        self.debt_type_var = ctk.StringVar(value="Lent")
        self.debt_toggle = ctk.CTkSegmentedButton(
            input_grid, 
            values=["Lent", "Borrowed"], 
            variable=self.debt_type_var, 
            height=UI_H,
            width=220,  # CRITICAL: Fixed width forces equal segment sizes
            selected_color=BRAND_ACCENT,
            unselected_color="#1a1a1a",
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        self.debt_toggle.pack(side="left", padx=(0, 10))
        
        btn_secure = ctk.CTkButton(input_grid, text="SECURE IOU", fg_color="white", 
                                   text_color="black", height=UI_H, # Locked Height
                                   font=ctk.CTkFont(family="Segoe UI", weight="bold"),
                                   hover_color="#e0e0e0", corner_radius=10,
                                   command=self.execute_iou_creation)
        btn_secure.pack(side="left")

        # --- SECTION 3: SPLIT LEDGER DISPLAY ---
        ledger_container = ctk.CTkFrame(self.debt_frame, fg_color="transparent")
        ledger_container.pack(pady=10, padx=40, fill="both", expand=True)
        ledger_container.grid_columnconfigure((0, 1), weight=1, uniform="a")
        
        # Owed To You Column
        lent_container = ctk.CTkFrame(ledger_container, fg_color="transparent")
        lent_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(lent_container, text="ASSETS (OWED TO YOU)", 
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), 
                     text_color=BRAND_ACCENT).pack(anchor="w", padx=10, pady=(0, 10))
        
        self.lent_scroll = ctk.CTkScrollableFrame(lent_container, fg_color="transparent", 
                                                  scrollbar_button_color="#1a1a1a")
        self.lent_scroll.pack(fill="both", expand=True)
        
        # You Owe Column
        borrow_container = ctk.CTkFrame(ledger_container, fg_color="transparent")
        borrow_container.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        ctk.CTkLabel(borrow_container, text="LIABILITIES (YOU OWE)", 
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), 
                     text_color="#ff4444").pack(anchor="w", padx=10, pady=(0, 10))
        
        self.borrowed_scroll = ctk.CTkScrollableFrame(borrow_container, fg_color="transparent", 
                                                      scrollbar_button_color="#1a1a1a")
        self.borrowed_scroll.pack(fill="both", expand=True)
        
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

    def refresh_all_data(self):
        """Forces a global B-tree re-scan and UI refresh."""
        self.needs_refresh = {k: True for k in self.needs_refresh}
        
        # Force the active screen to rebuild immediately
        self.refresh_dashboard_data() 
        self.refresh_vault_data()
        self.refresh_task_data()
        self.refresh_telemetry_data()
        self.refresh_debt_data()
        
        SystemMessageDialog("Sync Complete", "All local vaults and transaction tapes have been synchronized with the SQLite engine.", BRAND_ACCENT)

    def export_to_csv(self):
        """Standard IO Protocol for data portability."""
        try:
            # Execute the backend function
            generated_file = export_data_to_csv()
            SystemMessageDialog("Export Success", f"Financial data has been compiled into '{generated_file}' in your root directory.", BRAND_ACCENT)
        except Exception as e:
            SystemMessageDialog("Export Failed", f"OS Error: {e}", "#ff4444")

    def trigger_system_reset(self):
        """High-Authority Purge with Confirmation."""
        confirm = CustomConfirmDialog("Factory Reset", "This will permanently wipe all Vaults, Transactions, and Tasks. This action cannot be reversed.")
        
        # Wait for the user to make a choice
        if confirm.get_result():
            try:
                # Execute the backend DB wipe
                reset_database_registry()
                
                # Force the UI to reflect the empty database
                self.refresh_all_data() 
                
                SystemMessageDialog("System Purged", "Registry has been wiped. Operating System rebooted to default state.", "#ff4444")
            except Exception as e:
                SystemMessageDialog("Purge Failed", f"Database lock or execution error: {e}", "#ff4444")

if __name__ == "__main__":
    # The First Boot Protocol
    if not DB_PATH.exists():
        print("System OS: First boot detected. Building matrix architecture...")
        initialize_database()
        seed_default_categories()
        
    app = ApexFinanceApp()
    app.mainloop()