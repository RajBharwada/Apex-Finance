import customtkinter as ctk

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
        
        # Placeholder text for the main frame
        self.header = ctk.CTkLabel(self.main_frame, text="System Online. Awaiting Database Connection.", font=ctk.CTkFont(size=18))
        self.header.pack(pady=50)
        
    # UI Routing method
    def open_dashboard(self):
        self.header.configure(text="Dashboard Routing Active...")
        
    def open_tasks(self):
        self.header.configure(text="Task Tracker Routing Active...")
        
if __name__ == "__main__":
    app = ApexFinanceApp()
    app.mainloop()