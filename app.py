import tkinter as tk
from tkinter import ttk, messagebox
import oracledb
from datetime import datetime
import re

class RentalSystemApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tech Gear Rental System")
        self.root.geometry("1000x600")
        
        # Database connection
        try:
            self.conn = oracledb.connect(user="DEISHAUN", password="4313", dsn="localhost/xepdb1")
            self.cursor = self.conn.cursor()
        except oracledb.Error as e:
            messagebox.showerror("Database Error", f"Failed to connect: {e}")
            self.root.destroy()
            return
        
        # User session
        self.current_user_id = None
        self.current_role = None
        
        # Create main container
        self.container = ttk.Frame(self.root)
        self.container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Login screen
        self.show_login_screen()
    
    def show_login_screen(self):
        # Clear container
        for widget in self.container.winfo_children():
            widget.destroy()
        
        # Login frame
        login_frame = ttk.LabelFrame(self.container, text="Login")
        login_frame.pack(pady=20, padx=20, fill="both")
        
        # Email
        ttk.Label(login_frame, text="Email:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.email_entry = ttk.Entry(login_frame)
        self.email_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Password
        ttk.Label(login_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.password_entry = ttk.Entry(login_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Login button
        ttk.Button(login_frame, text="Login", command=self.handle_login).grid(row=2, column=0, columnspan=2, pady=10)
        
        # Register button
        ttk.Button(login_frame, text="Register", command=self.show_register_screen).grid(row=3, column=0, columnspan=2, pady=5)
    
    def handle_login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not email or not password:
            messagebox.showerror("Error", "Email and password are required")
            return
        
        try:
            self.cursor.execute("SELECT pkg_user_ops.verify_user(:email, :password) FROM dual",
                             {"email": email, "password": password})
            user_id = self.cursor.fetchone()[0]
            
            if user_id == 0:
                messagebox.showerror("Error", "Invalid email or password")
                return
            
            # Fetch user role
            self.cursor.execute("SELECT role FROM Users WHERE user_id = :id", {"id": user_id})
            self.current_role = self.cursor.fetchone()[0]
            self.current_user_id = user_id
            
            self.show_main_app()
        except oracledb.Error as e:
            messagebox.showerror("Database Error", f"Login failed: {e}")
    
    def show_register_screen(self):
        # Clear container
        for widget in self.container.winfo_children():
            widget.destroy()
        
        # Register frame
        reg_frame = ttk.LabelFrame(self.container, text="Register")
        reg_frame.pack(pady=20, padx=20, fill="both")
        
        # Name
        ttk.Label(reg_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.reg_name = ttk.Entry(reg_frame)
        self.reg_name.grid(row=0, column=1, padx=5, pady=5)
        
        # Email
        ttk.Label(reg_frame, text="Email:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.reg_email = ttk.Entry(reg_frame)
        self.reg_email.grid(row=1, column=1, padx=5, pady=5)
        
        # Phone
        ttk.Label(reg_frame, text="Phone (optional):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.reg_phone = ttk.Entry(reg_frame)
        self.reg_phone.grid(row=2, column=1, padx=5, pady=5)
        
        # Password
        ttk.Label(reg_frame, text="Password:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.reg_password = ttk.Entry(reg_frame, show="*")
        self.reg_password.grid(row=3, column=1, padx=5, pady=5)
        
        # Role
        ttk.Label(reg_frame, text="Role:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.reg_role = ttk.Combobox(reg_frame, values=["CUSTOMER", "ADMIN"], state="readonly")
        self.reg_role.set("CUSTOMER")
        self.reg_role.grid(row=4, column=1, padx=5, pady=5)
        
        # Buttons
        ttk.Button(reg_frame, text="Register", command=self.handle_register).grid(row=5, column=0, pady=10)
        ttk.Button(reg_frame, text="Back to Login", command=self.show_login_screen).grid(row=5, column=1, pady=10)
    
    def handle_register(self):
        name = self.reg_name.get().strip()
        email = self.reg_email.get().strip()
        phone = self.reg_phone.get().strip() or None
        password = self.reg_password.get().strip()
        role = self.reg_role.get()
        
        if not name or not email or not password:
            messagebox.showerror("Error", "Name, email, and password are required")
            return
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showerror("Error", "Invalid email format")
            return
        
        try:
            self.cursor.execute("""
                BEGIN
                    pkg_user_ops.register_user(:name, :email, :phone, :password, :role);
                    COMMIT;
                END;
            """, {"name": name, "email": email, "phone": phone, "password": password, "role": role})
            messagebox.showinfo("Success", "Registration successful! Please login.")
            self.show_login_screen()
        except oracledb.Error as e:
            error_code = e.args[0].code
            if error_code == 20014:
                messagebox.showerror("Error", "Name and email are required")
            elif error_code == 20054:
                messagebox.showerror("Error", "Password is required")
            elif error_code == 20055:
                messagebox.showerror("Error", "Invalid role")
            elif "ORA-00001" in e.args[0].message:
                messagebox.showerror("Error", "Email already registered")
            else:
                messagebox.showerror("Database Error", f"Registration failed: {e}")
    
    def show_main_app(self):
        # Clear container
        for widget in self.container.winfo_children():
            widget.destroy()
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.container)
        self.notebook.pack(fill="both", expand=True)
        
        # Create tabs
        self.user_tab = ttk.Frame(self.notebook)
        self.gear_tab = ttk.Frame(self.notebook)
        self.rental_tab = ttk.Frame(self.notebook)
        self.subscription_tab = ttk.Frame(self.notebook)
        self.payment_tab = ttk.Frame(self.notebook)
        self.penalty_tab = ttk.Frame(self.notebook)
        self.audit_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.user_tab, text="Users")
        self.notebook.add(self.gear_tab, text="Gear")
        self.notebook.add(self.rental_tab, text="Rentals")
        self.notebook.add(self.subscription_tab, text="Subscriptions")
        self.notebook.add(self.payment_tab, text="Payments")
        self.notebook.add(self.penalty_tab, text="Penalties")
        if self.current_role == "ADMIN":
            self.notebook.add(self.audit_tab, text="Audit Log")
        
        # Logout button
        ttk.Button(self.container, text="Logout", command=self.logout).pack(pady=5)
        
        # Initialize tabs
        self.setup_user_tab()
        self.setup_gear_tab()
        self.setup_rental_tab()
        self.setup_subscription_tab()
        self.setup_payment_tab()
        self.setup_penalty_tab()
        if self.current_role == "ADMIN":
            self.setup_audit_tab()
    
    def logout(self):
        self.current_user_id = None
        self.current_role = None
        self.show_login_screen()
    
    def setup_user_tab(self):
        frame = ttk.LabelFrame(self.user_tab, text="User Management")
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # User info
        ttk.Label(frame, text="Your Info:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.user_info = tk.Text(frame, height=3, width=50, state="disabled")
        self.user_info.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        ttk.Button(frame, text="Refresh Info", command=self.refresh_user_info).grid(row=2, column=0, pady=5)
        
        # Deactivate (admin or self)
        ttk.Button(frame, text="Deactivate Account", command=self.deactivate_user).grid(row=2, column=1, pady=5)
        
        self.refresh_user_info()
    
    def refresh_user_info(self):
        try:
            self.cursor.execute("SELECT pkg_user_ops.get_user_info(:id) FROM dual",
                             {"id": self.current_user_id})
            info = self.cursor.fetchone()[0]
            self.user_info.config(state="normal")
            self.user_info.delete(1.0, tk.END)
            self.user_info.insert(tk.END, info)
            self.user_info.config(state="disabled")
        except oracledb.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch user info: {e}")
    
    def deactivate_user(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to deactivate your account?"):
            try:
                self.cursor.execute("""
                    BEGIN
                        pkg_user_ops.deactivate_user(:id);
                        COMMIT;
                    END;
                """, {"id": self.current_user_id})
                messagebox.showinfo("Success", "Account deactivated")
                self.logout()
            except oracledb.Error as e:
                error_code = e.args[0].code
                if error_code == 20015:
                    messagebox.showerror("Error", "User does not exist")
                else:
                    messagebox.showerror("Database Error", f"Deactivation failed: {e}")
    
    def setup_gear_tab(self):
        frame = ttk.LabelFrame(self.gear_tab, text="Gear Management")
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Gear list with scrollbar
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        columns = ("ID", "Name", "Category", "Brand", "Rent Price", "Sub Price")
        if self.current_role == "ADMIN":
            columns += ("Stock",)
        self.gear_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        self.gear_tree.heading("ID", text="ID")
        self.gear_tree.heading("Name", text="Name")
        self.gear_tree.heading("Category", text="Category")
        self.gear_tree.heading("Brand", text="Brand")
        self.gear_tree.heading("Rent Price", text="Rent/Day")
        self.gear_tree.heading("Sub Price", text="Sub/Month")
        if self.current_role == "ADMIN":
            self.gear_tree.heading("Stock", text="Stock")
        
        # Set column widths
        self.gear_tree.column("ID", width=50)
        self.gear_tree.column("Name", width=150)
        self.gear_tree.column("Category", width=100)
        self.gear_tree.column("Brand", width=100)
        self.gear_tree.column("Rent Price", width=80)
        self.gear_tree.column("Sub Price", width=80)
        if self.current_role == "ADMIN":
            self.gear_tree.column("Stock", width=60)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.gear_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.gear_tree.xview)
        self.gear_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.gear_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Admin add gear
        if self.current_role == "ADMIN":
            add_frame = ttk.LabelFrame(frame, text="Add Gear")
            add_frame.pack(fill="x", padx=5, pady=5)
            
            ttk.Label(add_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5)
            self.gear_name = ttk.Entry(add_frame)
            self.gear_name.grid(row=0, column=1, padx=5, pady=5)
            
            ttk.Label(add_frame, text="Category:").grid(row=0, column=2, padx=5, pady=5)
            self.gear_category = ttk.Entry(add_frame)
            self.gear_category.grid(row=0, column=3, padx=5, pady=5)
            
            ttk.Label(add_frame, text="Brand:").grid(row=1, column=0, padx=5, pady=5)
            self.gear_brand = ttk.Entry(add_frame)
            self.gear_brand.grid(row=1, column=1, padx=5, pady=5)
            
            ttk.Label(add_frame, text="Rent Price/Day:").grid(row=1, column=2, padx=5, pady=5)
            self.gear_rent_price = ttk.Entry(add_frame)
            self.gear_rent_price.grid(row=1, column=3, padx=5, pady=5)
            
            ttk.Label(add_frame, text="Sub Price/Month:").grid(row=2, column=0, padx=5, pady=5)
            self.gear_sub_price = ttk.Entry(add_frame)
            self.gear_sub_price.grid(row=2, column=1, padx=5, pady=5)
            
            ttk.Label(add_frame, text="Stock:").grid(row=2, column=2, padx=5, pady=5)
            self.gear_stock = ttk.Entry(add_frame)
            self.gear_stock.grid(row=2, column=3, padx=5, pady=5)
            
            ttk.Button(add_frame, text="Add Gear", command=self.add_gear).grid(row=3, column=0, columnspan=4, pady=5)
            
            # Admin update stock
            update_frame = ttk.LabelFrame(frame, text="Update Stock")
            update_frame.pack(fill="x", padx=5, pady=5)
            
            ttk.Label(update_frame, text="Gear ID:").grid(row=0, column=0, padx=5, pady=5)
            self.update_gear_id = ttk.Entry(update_frame)
            self.update_gear_id.grid(row=0, column=1, padx=5, pady=5)
            
            ttk.Label(update_frame, text="Quantity (positive to add, negative to remove):").grid(row=0, column=2, padx=5, pady=5)
            self.update_qty = ttk.Entry(update_frame)
            self.update_qty.grid(row=0, column=3, padx=5, pady=5)
            
            ttk.Button(update_frame, text="Update Stock", command=self.update_stock).grid(row=1, column=0, columnspan=4, pady=5)
        
        ttk.Button(frame, text="Refresh", command=self.refresh_gear).pack(pady=5)
        self.refresh_gear()
    
    def refresh_gear(self):
        for item in self.gear_tree.get_children():
            self.gear_tree.delete(item)
        try:
            self.cursor.execute("SELECT gear_id, name, category, brand, rent_price_per_day, sub_price_per_month, stock FROM v_available_gear")
            for row in self.cursor:
                if self.current_role == "ADMIN":
                    self.gear_tree.insert("", tk.END, values=row)
                else:
                    self.gear_tree.insert("", tk.END, values=row[:-1])
        except oracledb.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch gear: {e}")
    
    def add_gear(self):
        name = self.gear_name.get().strip()
        category = self.gear_category.get().strip() or None
        brand = self.gear_brand.get().strip() or None
        try:
            rent_price = float(self.gear_rent_price.get().strip())
            sub_price = float(self.gear_sub_price.get().strip())
            stock = int(self.gear_stock.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Prices and stock must be valid numbers")
            return
        
        if not name:
            messagebox.showerror("Error", "Gear name is required")
            return
        
        try:
            self.cursor.execute("""
                BEGIN
                    pkg_gear_ops.add_gear(:user_id, :name, :category, :brand, :rent_price, :sub_price, :stock);
                    COMMIT;
                END;
            """, {
                "user_id": self.current_user_id,
                "name": name,
                "category": category,
                "brand": brand,
                "rent_price": rent_price,
                "sub_price": sub_price,
                "stock": stock
            })
            messagebox.showinfo("Success", "Gear added successfully")
            self.refresh_gear()
            # Clear entries
            self.gear_name.delete(0, tk.END)
            self.gear_category.delete(0, tk.END)
            self.gear_brand.delete(0, tk.END)
            self.gear_rent_price.delete(0, tk.END)
            self.gear_sub_price.delete(0, tk.END)
            self.gear_stock.delete(0, tk.END)
        except oracledb.Error as e:
            error_code = e.args[0].code
            if error_code == 20052:
                messagebox.showerror("Error", "Only admins can add gear")
            elif error_code == 20016:
                messagebox.showerror("Error", "Gear name is required")
            elif error_code == 20017:
                messagebox.showerror("Error", "Prices and stock cannot be negative")
            elif error_code == 20015:
                messagebox.showerror("Error", "User does not exist")
            elif "ORA-00001" in e.args[0].message:
                messagebox.showerror("Error", "Gear name already exists")
            else:
                messagebox.showerror("Database Error", f"Add gear failed: {e}")
    
    def update_stock(self):
        try:
            gear_id = int(self.update_gear_id.get().strip())
            qty = int(self.update_qty.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Gear ID and quantity must be valid numbers")
            return
        
        try:
            self.cursor.execute("""
                BEGIN
                    pkg_gear_ops.update_stock(:gear_id, :qty);
                    COMMIT;
                END;
            """, {
                "gear_id": gear_id,
                "qty": qty
            })
            messagebox.showinfo("Success", "Stock updated successfully")
            self.refresh_gear()
            self.update_gear_id.delete(0, tk.END)
            self.update_qty.delete(0, tk.END)
        except oracledb.Error as e:
            error_code = e.args[0].code
            if error_code == 20018:
                messagebox.showerror("Error", "Gear does not exist")
            elif error_code == 20019:
                messagebox.showerror("Error", "Stock update failed")
            else:
                messagebox.showerror("Database Error", f"Update stock failed: {e}")
    
    def setup_rental_tab(self):
        frame = ttk.LabelFrame(self.rental_tab, text="Rental Management")
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Rental list with scrollbar
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.rental_tree = ttk.Treeview(tree_frame, columns=("ID", "User", "Gear", "Start", "End", "Return", "Status", "Condition"), show="headings")
        self.rental_tree.heading("ID", text="ID")
        self.rental_tree.heading("User", text="User")
        self.rental_tree.heading("Gear", text="Gear")
        self.rental_tree.heading("Start", text="Start Date")
        self.rental_tree.heading("End", text="End Date")
        self.rental_tree.heading("Return", text="Return Date")
        self.rental_tree.heading("Status", text="Status")
        self.rental_tree.heading("Condition", text="Condition")
        
        # Set column widths
        self.rental_tree.column("ID", width=50)
        self.rental_tree.column("User", width=100)
        self.rental_tree.column("Gear", width=150)
        self.rental_tree.column("Start", width=100)
        self.rental_tree.column("End", width=100)
        self.rental_tree.column("Return", width=100)
        self.rental_tree.column("Status", width=80)
        self.rental_tree.column("Condition", width=80)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.rental_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.rental_tree.xview)
        self.rental_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.rental_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Rent gear
        rent_frame = ttk.LabelFrame(frame, text="Rent Gear")
        rent_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(rent_frame, text="Gear ID:").grid(row=0, column=0, padx=5, pady=5)
        self.rent_gear_id = ttk.Entry(rent_frame)
        self.rent_gear_id.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(rent_frame, text="Start Date (YYYY-MM-DD):").grid(row=0, column=2, padx=5, pady=5)
        self.rent_start = ttk.Entry(rent_frame)
        self.rent_start.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(rent_frame, text="End Date (YYYY-MM-DD):").grid(row=1, column=2, padx=5, pady=5)
        self.rent_end = ttk.Entry(rent_frame)
        self.rent_end.grid(row=1, column=3, padx=5, pady=5)
        
        ttk.Button(rent_frame, text="Rent Gear", command=self.rent_gear).grid(row=2, column=0, columnspan=4, pady=5)
        
        # Return gear
        return_frame = ttk.LabelFrame(frame, text="Return Gear")
        return_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(return_frame, text="Rental ID:").grid(row=0, column=0, padx=5, pady=5)
        self.return_rent_id = ttk.Entry(return_frame)
        self.return_rent_id.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(return_frame, text="Condition:").grid(row=0, column=2, padx=5, pady=5)
        self.return_condition = ttk.Combobox(return_frame, values=["GOOD", "DAMAGED", "BROKEN"], state="readonly")
        self.return_condition.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(return_frame, text="Return Gear", command=self.return_gear).grid(row=1, column=0, columnspan=4, pady=5)
        
        ttk.Button(frame, text="Refresh", command=self.refresh_rentals).pack(pady=5)
        self.refresh_rentals()
    
    def refresh_rentals(self):
        for item in self.rental_tree.get_children():
            self.rental_tree.delete(item)
        try:
            query = """
                SELECT rent_id, user_name, gear_name, start_date, end_date, return_date, status, condition_returned 
                FROM v_user_rentals
            """
            params = {}
            if self.current_role != "ADMIN":
                query += " WHERE user_id = :id AND status = 'RENTED'"
                params["id"] = self.current_user_id
            self.cursor.execute(query, params)
            for row in self.cursor:
                self.rental_tree.insert("", tk.END, values=row)
        except oracledb.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch rentals: {e}")
    
    def rent_gear(self):
        try:
            gear_id = int(self.rent_gear_id.get().strip())
            start_date = self.rent_start.get().strip()
            end_date = self.rent_end.get().strip() or None
        except ValueError:
            messagebox.showerror("Error", "Gear ID must be a number")
            return
        
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
        except ValueError:
            messagebox.showerror("Error", "Dates must be in YYYY-MM-DD format")
            return
        
        try:
            self.cursor.execute("""
                BEGIN
                    pkg_rental_ops.rent_gear(:user_id, :gear_id, TO_DATE(:start, 'YYYY-MM-DD'), 
                                             TO_DATE(:end, 'YYYY-MM-DD'));
                    COMMIT;
                END;
            """, {
                "user_id": self.current_user_id,
                "gear_id": gear_id,
                "start": start_date,
                "end": end_date
            })
            messagebox.showinfo("Success", "Gear rented successfully")
            self.refresh_rentals()
            self.refresh_gear()
            self.rent_gear_id.delete(0, tk.END)
            self.rent_start.delete(0, tk.END)
            self.rent_end.delete(0, tk.END)
        except oracledb.Error as e:
            error_code = e.args[0].code
            if error_code == 20021:
                messagebox.showerror("Error", "User does not exist")
            elif error_code == 20022:
                messagebox.showerror("Error", "Gear does not exist")
            elif error_code == 20023:
                messagebox.showerror("Error", "Gear not available for rent")
            elif error_code == 20053:
                messagebox.showerror("Error", "User has reached rental limit of 3 active rentals")
            elif "ORA-00001" in e.args[0].message:
                messagebox.showerror("Error", "Rental already exists for this user, gear, and start date")
            else:
                messagebox.showerror("Database Error", f"Rent gear failed: {e}")
    
    def return_gear(self):
        try:
            rent_id = int(self.return_rent_id.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Rental ID must be a number")
            return
        
        condition = self.return_condition.get()
        if not condition:
            messagebox.showerror("Error", "Condition is required")
            return
        
        try:
            # Calculate rental charge
            self.cursor.execute("SELECT pkg_rental_ops.calc_rental_charge(:rent_id) FROM dual",
                             {"rent_id": rent_id})
            charge = self.cursor.fetchone()[0]
            
            # Return gear
            self.cursor.execute("""
                BEGIN
                    pkg_rental_ops.return_gear(:rent_id, SYSDATE, :condition);
                    COMMIT;
                END;
            """, {"rent_id": rent_id, "condition": condition})
            
            # Prompt for payment
            if messagebox.askyesno("Payment Required", f"Rental charge: ${charge:.2f}. Proceed with payment?"):
                self.cursor.execute("""
                    BEGIN
                        pkg_payment_gateway.make_payment(:user_id, :type, :ref_id, :amount);
                        COMMIT;
                    END;
                """, {
                    "user_id": self.current_user_id,
                    "type": "RENTAL",
                    "ref_id": rent_id,
                    "amount": charge
                })
                messagebox.showinfo("Success", "Gear returned and payment made successfully")
            else:
                messagebox.showwarning("Warning", "Payment not made. Gear returned, but payment is pending.")
            
            self.refresh_rentals()
            self.refresh_gear()
            self.refresh_penalties()
            self.return_rent_id.delete(0, tk.END)
            self.return_condition.set("")
        except oracledb.Error as e:
            error_code = e.args[0].code
            if error_code == 20024:
                messagebox.showerror("Error", "Rental does not exist")
            elif error_code == 20056:
                messagebox.showerror("Error", "Invalid condition")
            elif error_code == 20025:
                messagebox.showerror("Error", "Rental does not exist")
            elif error_code == 20031:
                messagebox.showerror("Error", "User does not exist")
            elif error_code == 20032:
                messagebox.showerror("Error", "Payment amount cannot be negative")
            elif error_code == 20033:
                messagebox.showerror("Error", "Invalid payment type")
            elif error_code == 20034:
                messagebox.showerror("Error", "Invalid reference for payment")
            else:
                messagebox.showerror("Database Error", f"Return gear failed: {e}")
    
    def setup_subscription_tab(self):
        frame = ttk.LabelFrame(self.subscription_tab, text="Subscription Management")
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Subscription list with scrollbar
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.sub_tree = ttk.Treeview(tree_frame, columns=("ID", "User", "Gear", "Start", "End", "Active"), show="headings")
        self.sub_tree.heading("ID", text="ID")
        self.sub_tree.heading("User", text="User")
        self.sub_tree.heading("Gear", text="Gear")
        self.sub_tree.heading("Start", text="Start Date")
        self.sub_tree.heading("End", text="End Date")
        self.sub_tree.heading("Active", text="Active")
        
        # Set column widths
        self.sub_tree.column("ID", width=50)
        self.sub_tree.column("User", width=100)
        self.sub_tree.column("Gear", width=150)
        self.sub_tree.column("Start", width=100)
        self.sub_tree.column("End", width=100)
        self.sub_tree.column("Active", width=60)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.sub_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.sub_tree.xview)
        self.sub_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.sub_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Subscribe
        sub_frame = ttk.LabelFrame(frame, text="Subscribe to Gear")
        sub_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(sub_frame, text="Gear ID:").grid(row=0, column=0, padx=5, pady=5)
        self.sub_gear_id = ttk.Entry(sub_frame)
        self.sub_gear_id.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(sub_frame, text="Start Date (YYYY-MM-DD):").grid(row=0, column=2, padx=5, pady=5)
        self.sub_start = ttk.Entry(sub_frame)
        self.sub_start.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(sub_frame, text="End Date (YYYY-MM-DD):").grid(row=1, column=2, padx=5, pady=5)
        self.sub_end = ttk.Entry(sub_frame)
        self.sub_end.grid(row=1, column=3, padx=5, pady=5)
        
        ttk.Button(sub_frame, text="Subscribe", command=self.subscribe_gear).grid(row=2, column=0, columnspan=4, pady=5)
        
        # Cancel subscription
        cancel_frame = ttk.LabelFrame(frame, text="Cancel Subscription")
        cancel_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(cancel_frame, text="Subscription ID:").grid(row=0, column=0, padx=5, pady=5)
        self.cancel_sub_id = ttk.Entry(cancel_frame)
        self.cancel_sub_id.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(cancel_frame, text="Cancel Subscription", command=self.cancel_subscription).grid(row=1, column=0, columnspan=2, pady=5)
        
        ttk.Button(frame, text="Refresh", command=self.refresh_subscriptions).pack(pady=5)
        self.refresh_subscriptions()
    
    def refresh_subscriptions(self):
        for item in self.sub_tree.get_children():
            self.sub_tree.delete(item)
        try:
            query = "SELECT sub_id, user_name, gear_name, start_date, end_date, is_active FROM v_user_subscriptions"
            params = {}
            if self.current_role != "ADMIN":
                query += " WHERE user_id = :id AND is_active = 'Y'"
                params["id"] = self.current_user_id
            self.cursor.execute(query, params)
            for row in self.cursor:
                self.sub_tree.insert("", tk.END, values=row)
        except oracledb.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch subscriptions: {e}")
    
    def subscribe_gear(self):
        try:
            gear_id = int(self.sub_gear_id.get().strip())
            start_date = self.sub_start.get().strip()
            end_date = self.sub_end.get().strip()
        except ValueError:
            messagebox.showerror("Error", "Gear ID must be a number")
            return
        
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Dates must be in YYYY-MM-DD format")
            return
        
        try:
            self.cursor.execute("""
                BEGIN
                    pkg_subscription_service.subscribe_gear(:user_id, :gear_id, 
                        TO_DATE(:start, 'YYYY-MM-DD'), TO_DATE(:end, 'YYYY-MM-DD'));
                    COMMIT;
                END;
            """, {
                "user_id": self.current_user_id,
                "gear_id": gear_id,
                "start": start_date,
                "end": end_date
            })
            messagebox.showinfo("Success", "Subscribed successfully")
            self.refresh_subscriptions()
            self.sub_gear_id.delete(0, tk.END)
            self.sub_start.delete(0, tk.END)
            self.sub_end.delete(0, tk.END)
        except oracledb.Error as e:
            error_code = e.args[0].code
            if error_code == 20026:
                messagebox.showerror("Error", "User does not exist")
            elif error_code == 20027:
                messagebox.showerror("Error", "Gear does not exist")
            elif error_code == 20028:
                messagebox.showerror("Error", "End date cannot be before start date")
            elif error_code == 20029:
                messagebox.showerror("Error", "User already has an active subscription for this gear")
            elif "ORA-00001" in e.args[0].message:
                messagebox.showerror("Error", "Subscription already exists for this user, gear, and start date")
            else:
                messagebox.showerror("Database Error", f"Subscription failed: {e}")
    
    def cancel_subscription(self):
        try:
            sub_id = int(self.cancel_sub_id.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Subscription ID must be a number")
            return
        
        try:
            # Check if subscription exists
            self.cursor.execute("""
                SELECT COUNT(*) 
                FROM Subscriptions 
                WHERE sub_id = :sub_id
            """, {"sub_id": sub_id})
            exists = self.cursor.fetchone()[0]
            if exists == 0:
                messagebox.showerror("Error", "Subscription does not exist")
                return
            
            # Calculate subscription charge (days used * rent_price_per_day)
            self.cursor.execute("""
                SELECT s.start_date, NVL(s.end_date, SYSDATE), g.rent_price_per_day
                FROM Subscriptions s
                JOIN Gear g ON s.gear_id = g.gear_id
                WHERE s.sub_id = :sub_id
            """, {"sub_id": sub_id})
            result = self.cursor.fetchone()
            if result:
                start_date, end_date, rent_price = result
                days_used = (end_date - start_date).days + 1
                charge = days_used * rent_price
            else:
                messagebox.showerror("Error", "Failed to fetch subscription details")
                return
            
            # Cancel subscription
            self.cursor.execute("""
                BEGIN
                    pkg_subscription_service.cancel_subscription(:sub_id);
                    COMMIT;
                END;
            """, {"sub_id": sub_id})
            
            # Prompt for payment
            if messagebox.askyesno("Payment Required", f"Subscription charge: ${charge:.2f}. Proceed with payment?"):
                self.cursor.execute("""
                    BEGIN
                        pkg_payment_gateway.make_payment(:user_id, :type, :ref_id, :amount);
                        COMMIT;
                    END;
                """, {
                    "user_id": self.current_user_id,
                    "type": "SUBSCRIPTION",
                    "ref_id": sub_id,
                    "amount": charge
                })
                messagebox.showinfo("Success", "Subscription cancelled and payment made successfully")
            else:
                messagebox.showwarning("Warning", "Payment not made. Subscription cancelled, but payment is pending.")
            
            self.refresh_subscriptions()
            self.cancel_sub_id.delete(0, tk.END)
        except oracledb.Error as e:
            error_code = e.args[0].code
            if error_code == 20030:
                messagebox.showerror("Error", "Subscription does not exist")
            elif error_code == 20031:
                messagebox.showerror("Error", "User does not exist")
            elif error_code == 20032:
                messagebox.showerror("Error", "Payment amount cannot be negative")
            elif error_code == 20033:
                messagebox.showerror("Error", "Invalid payment type")
            elif error_code == 20034:
                messagebox.showerror("Error", "Invalid reference for payment")
            elif error_code == 20063:
                messagebox.showerror("Error", "Subscription is already inactive")
            else:
                messagebox.showerror("Database Error", f"Cancel subscription failed: {e}")
    
    def setup_payment_tab(self):
        frame = ttk.LabelFrame(self.payment_tab, text="Payment Management")
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Payment list with scrollbar
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.payment_tree = ttk.Treeview(tree_frame, columns=("ID", "User", "Amount", "Date", "Type", "Ref ID"), show="headings")
        self.payment_tree.heading("ID", text="ID")
        self.payment_tree.heading("User", text="User ID")
        self.payment_tree.heading("Amount", text="Amount")
        self.payment_tree.heading("Date", text="Date")
        self.payment_tree.heading("Type", text="Type")
        self.payment_tree.heading("Ref ID", text="Ref ID")
        
        # Set column widths
        self.payment_tree.column("ID", width=50)
        self.payment_tree.column("User", width=80)
        self.payment_tree.column("Amount", width=80)
        self.payment_tree.column("Date", width=100)
        self.payment_tree.column("Type", width=100)
        self.payment_tree.column("Ref ID", width=80)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.payment_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.payment_tree.xview)
        self.payment_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.payment_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Make payment (for manual payments)
        pay_frame = ttk.LabelFrame(frame, text="Make Payment")
        pay_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(pay_frame, text="Type:").grid(row=0, column=0, padx=5, pady=5)
        self.pay_type = ttk.Combobox(pay_frame, values=["RENTAL", "SUBSCRIPTION", "PENALTY"], state="readonly")
        self.pay_type.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(pay_frame, text="Reference ID:").grid(row=0, column=2, padx=5, pady=5)
        self.pay_ref_id = ttk.Entry(pay_frame)
        self.pay_ref_id.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(pay_frame, text="Amount:").grid(row=1, column=0, padx=5, pady=5)
        self.pay_amount = ttk.Entry(pay_frame)
        self.pay_amount.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(pay_frame, text="Make Payment", command=self.make_payment).grid(row=2, column=0, columnspan=4, pady=5)
        
        ttk.Button(frame, text="Refresh", command=self.refresh_payments).pack(pady=5)
        self.refresh_payments()
    
    def refresh_payments(self):
        for item in self.payment_tree.get_children():
            self.payment_tree.delete(item)
        try:
            query = "SELECT payment_id, user_id, amount, payment_date, type, ref_id FROM Payments"
            params = {}
            if self.current_role != "ADMIN":
                query += " WHERE user_id = :id"
                params["id"] = self.current_user_id
            self.cursor.execute(query, params)
            for row in self.cursor:
                self.payment_tree.insert("", tk.END, values=row)
        except oracledb.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch payments: {e}")
    
    def make_payment(self):
        pay_type = self.pay_type.get()
        try:
            ref_id = int(self.pay_ref_id.get().strip())
            amount = float(self.pay_amount.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Reference ID and amount must be valid numbers")
            return
        
        if not pay_type:
            messagebox.showerror("Error", "Payment type is required")
            return
        
        try:
            self.cursor.execute("""
                BEGIN
                    pkg_payment_gateway.make_payment(:user_id, :type, :ref_id, :amount);
                    COMMIT;
                END;
            """, {
                "user_id": self.current_user_id,
                "type": pay_type,
                "ref_id": ref_id,
                "amount": amount
            })
            messagebox.showinfo("Success", "Payment made successfully")
            self.refresh_payments()
            self.pay_type.set("")
            self.pay_ref_id.delete(0, tk.END)
            self.pay_amount.delete(0, tk.END)
        except oracledb.Error as e:
            error_code = e.args[0].code
            if error_code == 20031:
                messagebox.showerror("Error", "User does not exist")
            elif error_code == 20032:
                messagebox.showerror("Error", "Payment amount cannot be negative")
            elif error_code == 20033:
                messagebox.showerror("Error", "Invalid payment type")
            elif error_code == 20034:
                messagebox.showerror("Error", "Invalid reference for the given payment type")
            elif error_code == 20062:
                messagebox.showerror("Error", "Payment already made for this reference")
            else:
                messagebox.showerror("Database Error", f"Payment failed: {e}")
    
    def setup_penalty_tab(self):
        frame = ttk.LabelFrame(self.penalty_tab, text="Penalty Management")
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Penalty list with scrollbar
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.penalty_tree = ttk.Treeview(tree_frame, columns=("ID", "Rent ID", "Amount", "Reason", "Status"), show="headings")
        self.penalty_tree.heading("ID", text="ID")
        self.penalty_tree.heading("Rent ID", text="Rent ID")
        self.penalty_tree.heading("Amount", text="Amount")
        self.penalty_tree.heading("Reason", text="Reason")
        self.penalty_tree.heading("Status", text="Status")
        
        # Set column widths
        self.penalty_tree.column("ID", width=50)
        self.penalty_tree.column("Rent ID", width=80)
        self.penalty_tree.column("Amount", width=80)
        self.penalty_tree.column("Reason", width=200)
        self.penalty_tree.column("Status", width=80)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.penalty_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.penalty_tree.xview)
        self.penalty_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.penalty_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Admin assign penalty
        if self.current_role == "ADMIN":
            assign_frame = ttk.LabelFrame(frame, text="Assign Penalty")
            assign_frame.pack(fill="x", padx=5, pady=5)
            
            ttk.Label(assign_frame, text="Rental ID:").grid(row=0, column=0, padx=5, pady=5)
            self.penalty_rent_id = ttk.Entry(assign_frame)
            self.penalty_rent_id.grid(row=0, column=1, padx=5, pady=5)
            
            ttk.Label(assign_frame, text="Reason:").grid(row=0, column=2, padx=5, pady=5)
            self.penalty_reason = ttk.Entry(assign_frame)
            self.penalty_reason.grid(row=0, column=3, padx=5, pady=5)
            
            ttk.Button(assign_frame, text="Assign Penalty", command=self.assign_penalty).grid(row=1, column=0, columnspan=4, pady=5)
        
        # Resolve penalty
        resolve_frame = ttk.LabelFrame(frame, text="Resolve Penalty")
        resolve_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(resolve_frame, text="Penalty ID:").grid(row=0, column=0, padx=5, pady=5)
        self.resolve_penalty_id = ttk.Entry(resolve_frame)
        self.resolve_penalty_id.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(resolve_frame, text="Resolve Penalty", command=self.resolve_penalty).grid(row=1, column=0, columnspan=2, pady=5)
        
        ttk.Button(frame, text="Refresh", command=self.refresh_penalties).pack(pady=5)
        self.refresh_penalties()
    
    def refresh_penalties(self):
        for item in self.penalty_tree.get_children():
            self.penalty_tree.delete(item)
        try:
            query = "SELECT penalty_id, rent_id, amount, reason, status FROM Penalties"
            params = {}
            if self.current_role != "ADMIN":
                query = """
                    SELECT p.penalty_id, p.rent_id, p.amount, p.reason, p.status
                    FROM Penalties p
                    JOIN Rentals r ON p.rent_id = r.rent_id
                    WHERE r.user_id = :id
                """
                params["id"] = self.current_user_id
            self.cursor.execute(query, params)
            for row in self.cursor:
                self.penalty_tree.insert("", tk.END, values=row)
        except oracledb.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch penalties: {e}")
    
    def assign_penalty(self):
        try:
            rent_id = int(self.penalty_rent_id.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Rental ID must be a number")
            return
        
        reason = self.penalty_reason.get().strip()
        if not reason:
            messagebox.showerror("Error", "Reason is required")
            return
        
        try:
            self.cursor.execute("""
                BEGIN
                    pkg_penalty_center.assign_penalty(:rent_id, :reason);
                    COMMIT;
                END;
            """, {"rent_id": rent_id, "reason": reason})
            messagebox.showinfo("Success", "Penalty assigned successfully")
            self.refresh_penalties()
            self.penalty_rent_id.delete(0, tk.END)
            self.penalty_reason.delete(0, tk.END)
        except oracledb.Error as e:
            error_code = e.args[0].code
            if error_code == 20034:
                messagebox.showerror("Error", "Rental does not exist")
            elif error_code == 20035:
                messagebox.showerror("Error", "No penalty applicable")
            elif error_code == 20036:
                messagebox.showerror("Error", "Rental is not overdue or has already been returned")
            else:
                messagebox.showerror("Database Error", f"Assign penalty failed: {e}")
    
    def resolve_penalty(self):
        try:
            penalty_id = int(self.resolve_penalty_id.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Penalty ID must be a number")
            return
        
        try:
            # Get penalty amount
            self.cursor.execute("SELECT amount FROM Penalties WHERE penalty_id = :id", {"id": penalty_id})
            result = self.cursor.fetchone()
            if not result:
                messagebox.showerror("Error", "Penalty does not exist")
                return
            amount = result[0]
            
            # Resolve penalty
            self.cursor.execute("""
                BEGIN
                    pkg_penalty_center.resolve_penalty(:penalty_id);
                    COMMIT;
                END;
            """, {"penalty_id": penalty_id})
            
            # For customers, enforce payment
            if self.current_role != "ADMIN":
                if messagebox.askyesno("Payment Required", f"Penalty amount: ${amount:.2f}. Proceed with payment?"):
                    self.cursor.execute("""
                        BEGIN
                            pkg_payment_gateway.make_payment(:user_id, :type, :ref_id, :amount);
                            COMMIT;
                        END;
                    """, {
                        "user_id": self.current_user_id,
                        "type": "PENALTY",
                        "ref_id": penalty_id,
                        "amount": amount
                    })
                    messagebox.showinfo("Success", "Penalty resolved and payment made successfully")
                else:
                    messagebox.showwarning("Warning", "Payment not made. Penalty resolved, but payment is pending.")
            else:
                messagebox.showinfo("Success", "Penalty resolved successfully")
            
            self.refresh_penalties()
            self.refresh_payments()
            self.resolve_penalty_id.delete(0, tk.END)
        except oracledb.Error as e:
            error_code = e.args[0].code
            if error_code == 20037:
                messagebox.showerror("Error", "Penalty does not exist")
            elif error_code == 20031:
                messagebox.showerror("Error", "User does not exist")
            elif error_code == 20032:
                messagebox.showerror("Error", "Payment amount cannot be negative")
            elif error_code == 20033:
                messagebox.showerror("Error", "Invalid payment type")
            elif error_code == 20034:
                messagebox.showerror("Error", "Invalid reference for payment")
            elif error_code == 20061:
                messagebox.showerror("Error", "Penalty has already been resolved and paid")
            else:
                messagebox.showerror("Database Error", f"Resolve penalty failed: {e}")
    
    def setup_audit_tab(self):
        frame = ttk.LabelFrame(self.audit_tab, text="Audit Log")
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Audit list with scrollbar
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.audit_tree = ttk.Treeview(tree_frame, columns=("ID", "User", "Table", "Action", "Timestamp", "Details"), show="headings")
        self.audit_tree.heading("ID", text="ID")
        self.audit_tree.heading("User", text="User ID")
        self.audit_tree.heading("Table", text="Table")
        self.audit_tree.heading("Action", text="Action")
        self.audit_tree.heading("Timestamp", text="Timestamp")
        self.audit_tree.heading("Details", text="Details")
        
        # Set column widths
        self.audit_tree.column("ID", width=50)
        self.audit_tree.column("User", width=80)
        self.audit_tree.column("Table", width=100)
        self.audit_tree.column("Action", width=100)
        self.audit_tree.column("Timestamp", width=100)
        self.audit_tree.column("Details", width=300)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.audit_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.audit_tree.xview)
        self.audit_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.audit_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Filter
        filter_frame = ttk.LabelFrame(frame, text="Filter Audit Log")
        filter_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Table Name:").grid(row=0, column=0, padx=5, pady=5)
        self.audit_table = ttk.Entry(filter_frame)
        self.audit_table.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Start Date (YYYY-MM-DD):").grid(row=0, column=2, padx=5, pady=5)
        self.audit_start = ttk.Entry(filter_frame)
        self.audit_start.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="End Date (YYYY-MM-DD):").grid(row=1, column=2, padx=5, pady=5)
        self.audit_end = ttk.Entry(filter_frame)
        self.audit_end.grid(row=1, column=3, padx=5, pady=5)
        
        ttk.Button(filter_frame, text="Search", command=self.search_audit).grid(row=2, column=0, columnspan=4, pady=5)
        
        ttk.Button(frame, text="Refresh", command=self.refresh_audit).pack(pady=5)
        self.refresh_audit()
    
    def refresh_audit(self):
        for item in self.audit_tree.get_children():
            self.audit_tree.delete(item)
        try:
            self.cursor.execute("""
                SELECT log_id, user_id, table_name, action, timestamp, details
                FROM Audit_Log
                ORDER BY timestamp DESC
            """)
            for row in self.cursor:
                self.audit_tree.insert("", tk.END, values=row)
        except oracledb.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch audit log: {e}")
    
    def search_audit(self):
        table_name = self.audit_table.get().strip() or None
        start_date = self.audit_start.get().strip()
        end_date = self.audit_end.get().strip()
        
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime.now()
            end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()
        except ValueError:
            messagebox.showerror("Error", "Dates must be in YYYY-MM-DD format")
            return
        
        try:
            self.cursor.callproc("pkg_audit_trail.get_audit_log", [
                table_name,
                start_date or datetime.now().strftime("%Y-%m-%d"),
                end_date or datetime.now().strftime("%Y-%m-%d"),
                self.cursor.var(oracledb.CURSOR)
            ])
            cursor = self.cursor.fetchall()[-1][3]
            for item in self.audit_tree.get_children():
                self.audit_tree.delete(item)
            for row in cursor:
                self.audit_tree.insert("", tk.END, values=row)
        except oracledb.Error as e:
            messagebox.showerror("Database Error", f"Audit search failed: {e}")
    
    def __del__(self):
        if hasattr(self, 'cursor'):
            self.cursor.close()
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = RentalSystemApp(root)
    root.mainloop()
