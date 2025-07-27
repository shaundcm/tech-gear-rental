# Tech Gear Rental System
Welcome to the Tech Gear Rental System! This is a desktop app built to make renting tech gear (like cameras, laptops, or drones) super smooth. It’s got a clean Tkinter GUI for users and a robust Oracle database backend to keep everything organized. Whether you’re a customer renting gear or an admin managing inventory, this system has you covered with features like rentals, subscriptions, payments, and even penalty tracking.
Features

* User Authentication: Sign up or log in with email and password. Supports admin and customer roles.
* Role-Based Access: Admins manage gear, assign penalties, and view audit logs; customers handle their rentals and subscriptions.
* Gear Management: Admins can add gear and update stock; everyone sees available gear with prices and stock details.
* Rentals & Subscriptions: Rent gear for a set period or subscribe monthly, with automatic stock updates.
* Payments & Penalties: Handle payments for rentals, subscriptions, or penalties. Admins can assign penalties for late returns or damage.
* Audit Logs: Admins can view and filter detailed logs of all system actions (e.g., gear added, rentals made).
* Error Handling: User-friendly error messages for invalid inputs or database issues.
* Data Integrity: Backend constraints and triggers ensure consistent data (e.g., no negative stock, max 3 active rentals).

## Tech Stack
* Frontend: Python with Tkinter for the GUI, oracledb for database connectivity.
* Backend: Oracle SQL with PL/SQL packages, views, and triggers.
* Database: Oracle Database (tested with XE 21c).

## Prerequisites
To run this project, you’ll need:

* Python 3.8+ with tkinter and oracledb libraries.
* Oracle Database (e.g., Oracle XE 21c) with the schema set up.
* Basic knowledge of SQL and PL/SQL for backend setup.

## Installation

### Clone the Repository:
```bash
git clone https://github.com/shaundcm/tech-gear-rental.git
cd tech-gear-rental
```

### Set Up Python Environment:
Install required Python packages:
```bash
pip install oracledb
```

Tkinter comes with Python, so no extra install is needed.

### Configure Oracle Database:

* Install Oracle Database Express Edition (XE) or any Oracle DB version.
* Run the backend SQL script (RentalSystem.sql) to create tables, packages, views, and triggers
```sqlplus /nolog
connect sys as sysdba
@path/to/backend.sql
```

Ensure the database user DEISHAUN with password 4313 is created, or update the connection string in app.py.

### Update Database Connection:
In app.py, modify the connection details if needed:
```python
self.conn = oracledb.connect(user="DEISHAUN", password="4313", dsn="localhost/xepdb1")
```

### Run the Application:
Start the frontend:
```bash
python app.py
```

## Usage
### Login or Register:

* Use the login screen to sign in with an email and password.
* New users can register as CUSTOMER or ADMIN.

### Navigate Tabs:

* Users: View your info or deactivate your account.
* Gear: Browse available gear. Admins can add gear or update stock.
* Rentals: Rent gear, return it, and make payments. Admins see all rentals.
* Subscriptions: Subscribe to gear or cancel subscriptions with payments.
* Payments: View payment history or make manual payments.
* Penalties: Resolve penalties (customers) or assign them (admins).
* Audit Log (Admins only): View or filter system actions by table or date.

### Example Actions:

* Customer: Rent a camera (Gear ID from Gear tab), return it, and pay the charge.
* Admin: Add a new laptop (e.g., name: "MacBook Pro", category: "Laptop", stock: 5), update its stock, or assign a penalty for a late rental.

## Project Structure

* backend.sql: Oracle SQL script with tables, packages, views, and triggers.
* app.py: Python Tkinter frontend for the GUI.
* README.md: This file.

## Notes

* Security: The current setup uses plain passwords and hardcoded credentials for simplicity. In production, use environment variables for credentials and implement password hashing (e.g., Oracle’s DBMS_CRYPTO).
* Improvements: Consider adding date pickers (e.g., tkcalendar), pending payment tracking, or gear update/delete options.
* Known Issue: Subscription cancellation uses daily rental prices instead of monthly. A fix is to prorate sub_price_per_month.

### Contributing: 
Feel free to fork the repo and submit pull requests!

### Ideas for improvement:
* Add a date picker for easier date input.
* Implement pending payment tracking in the Payments tab.
* Enhance admin features (e.g., user management, gear updates).

#### License
This project is licensed under the MIT License. See the LICENSE file for details.
#### Acknowledgments
Built as an academic project to explore GUI development with Tkinter and Oracle database integration. Thanks to the Python and Oracle communities for their awesome libraries and docs!
