import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "okeb_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Daily Sales
    c.execute('''CREATE TABLE IF NOT EXISTS daily_sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT, department TEXT, gross_revenue REAL, 
                    total_expenses REAL, net_cash REAL, submitted_by TEXT
                )''')
    
    # 2. POS Records (UPDATED COLUMNS)
    c.execute('''CREATE TABLE IF NOT EXISTS pos_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT, staff_name TEXT, machine_id TEXT, 
                    opening_cash REAL, opening_wallet REAL, capital_given REAL, 
                    total_deposits REAL, total_withdrawals REAL, free_vol REAL,
                    total_volume REAL, expected_comm REAL, actual_comm REAL, 
                    bank_charges REAL, net_profit REAL,
                    closing_cash REAL, closing_wallet REAL, calculated_balance REAL, status TEXT
                )''')

    # 3. Fuel Records
    c.execute('''CREATE TABLE IF NOT EXISTS fuel_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT, staff_name TEXT, 
                    p1_name TEXT, pump_a_open REAL, pump_a_close REAL,
                    p2_name TEXT, pump_b_open REAL, pump_b_close REAL,
                    total_liters REAL, unit_price REAL, expected_revenue REAL, 
                    cash_collected REAL, pos_collected REAL, credit_sales REAL, 
                    shortage_surplus REAL, customer_name TEXT
                )''')
    
    # 4. Bakery Records
    c.execute('''CREATE TABLE IF NOT EXISTS bakery_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT, staff_name TEXT, total_bread_sold INTEGER, 
                    total_damaged INTEGER, expected_revenue REAL, actual_revenue REAL, 
                    shortage_surplus REAL, note TEXT, credit_sales REAL, customer_name TEXT
                )''')

    # 5. Farm Records
    c.execute('''CREATE TABLE IF NOT EXISTS farm_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT, staff_name TEXT, customer_name TEXT, 
                    items_summary TEXT, total_value REAL, amount_paid REAL, 
                    payment_mode TEXT, balance_due REAL, note TEXT
                )''')

    # 6. Debts Table
    c.execute('''CREATE TABLE IF NOT EXISTS debts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT, department TEXT, customer_name TEXT, 
                    amount REAL, status TEXT
                )''')

    # 7. PRODUCT PRICES
    c.execute('''CREATE TABLE IF NOT EXISTS prices (
                    item_name TEXT PRIMARY KEY,
                    price REAL
                )''')
    
    c.execute("SELECT count(*) FROM prices")
    if c.fetchone()[0] == 0:
        defaults = [
            ("Big Jumbo", 1500), ("Small Jumbo", 800), ("Big Milk", 1200),
            ("Family Loaf", 1000), ("Sardine Bread", 2000), ("Big Toast", 1000),
            ("Small Toast", 500), ("Round Bread", 400),
            ("Fuel Unit Price", 700)
        ]
        c.executemany("INSERT INTO prices VALUES (?, ?)", defaults)
        conn.commit()
    
    conn.commit()
    conn.close()

# --- PRICE FUNCTIONS ---
def get_prices():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM prices")
    data = dict(c.fetchall())
    conn.close()
    return data

def update_price(item_name, new_price):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE prices SET price=? WHERE item_name=?", (new_price, item_name))
    conn.commit()
    conn.close()

# --- SAVE FUNCTIONS ---

def save_daily_report(dept, revenue, expenses, net_cash, user):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT INTO daily_sales (date, department, gross_revenue, total_expenses, net_cash, submitted_by) VALUES (?, ?, ?, ?, ?, ?)",
              (date_str, dept, revenue, expenses, net_cash, user))
    conn.commit()
    conn.close()

def save_pos_entry(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Updated insert to match new columns
    c.execute("""INSERT INTO pos_records 
                 (date, staff_name, machine_id, opening_cash, opening_wallet, capital_given, 
                  total_deposits, total_withdrawals, free_vol, total_volume, 
                  expected_comm, actual_comm, bank_charges, net_profit,
                  closing_cash, closing_wallet, calculated_balance, status) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (data['date'], data['staff'], data['machine'], data['open_cash'], data['open_wallet'], data['capital'], 
               data['deposits'], data['withdrawals'], data['free'], data['volume'],
               data['expected'], data['actual'], data['bank'], data['profit'],
               data['close_cash'], data['close_wallet'], data['balance'], data['status']))
    conn.commit()
    conn.close()
    # We save Net Profit as the revenue for the dashboard
    save_daily_report("POS", data['profit'], 0, data['profit'], data['staff'])

def save_fuel_entry(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    cust_label = "Multiple Debtors" if len(data.get('debtors_list', [])) > 0 else "None"
    c.execute("""INSERT INTO fuel_records (date, staff_name, p1_name, pump_a_open, pump_a_close, p2_name, pump_b_open, pump_b_close, total_liters, unit_price, expected_revenue, cash_collected, pos_collected, credit_sales, shortage_surplus, customer_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (data['date'], data['staff'], data['p1_name'], data['pA_open'], data['pA_close'], data['p2_name'], data['pB_open'], data['pB_close'], data['total_liters'], data['price'], data['expected'], data['cash'], data['pos'], data['credit'], data['diff'], cust_label))
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    for debtor in data.get('debtors_list', []):
        if debtor['amount'] > 0:
            c.execute("INSERT INTO debts (date, department, customer_name, amount, status) VALUES (?, ?, ?, ?, ?)",
                      (date_str, "FUEL", debtor['name'], debtor['amount'], "Unpaid"))
    conn.commit()
    conn.close()
    actual_rev = data['cash'] + data['pos']
    save_daily_report("FUEL", actual_rev, 0, actual_rev, data['staff'])

def save_bakery_entry(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    cust_label = "Multiple Debtors" if len(data.get('debtors_list', [])) > 0 else "None"
    c.execute("""INSERT INTO bakery_records (date, staff_name, total_bread_sold, total_damaged, expected_revenue, actual_revenue, shortage_surplus, note, credit_sales, customer_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (data['date'], data['staff'], data['sold_qty'], data['damaged_qty'], data['expected'], data['actual'], data['diff'], data['note'], data['credit'], cust_label))
    date_str = datetime.now().strftime("%Y-%m-%d")
    for debtor in data.get('debtors_list', []):
        if debtor['amount'] > 0:
            c.execute("INSERT INTO debts (date, department, customer_name, amount, status) VALUES (?, ?, ?, ?, ?)",
                      (date_str, "BAKERY", debtor['name'], debtor['amount'], "Unpaid"))
    conn.commit()
    conn.close()
    save_daily_report("BAKERY", data['actual'], 0, data['actual'], data['staff'])

def save_farm_entry(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""INSERT INTO farm_records (date, staff_name, customer_name, items_summary, total_value, amount_paid, payment_mode, balance_due, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (data['date'], data['staff'], data['customer'], data['items'], data['total'], data['paid'], data['mode'], data['balance'], data['note']))
    if data['balance'] > 0:
        date_str = datetime.now().strftime("%Y-%m-%d")
        c.execute("INSERT INTO debts (date, department, customer_name, amount, status) VALUES (?, ?, ?, ?, ?)",
                  (date_str, "FARM", data['customer'], data['balance'], "Unpaid"))
    conn.commit()
    conn.close()
    save_daily_report("FARM", data['paid'], 0, data['paid'], data['staff'])

# --- HISTORY FUNCTIONS ---

def get_dashboard_metrics():
    conn = sqlite3.connect(DB_NAME)
    try:
        df_sales = pd.read_sql_query("SELECT * FROM daily_sales", conn)
        rev = df_sales['gross_revenue'].sum() if not df_sales.empty else 0
        exp = df_sales['total_expenses'].sum() if not df_sales.empty else 0
        net = df_sales['net_cash'].sum() if not df_sales.empty else 0
        df_debts = pd.read_sql_query("SELECT * FROM debts WHERE status='Unpaid'", conn)
        total_debt = df_debts['amount'].sum() if not df_debts.empty else 0
        recent_debts = df_debts.tail(5)
    except:
        rev, exp, net, total_debt = 0, 0, 0, 0
        recent_debts = pd.DataFrame()
    conn.close()
    return rev, exp, net, total_debt, recent_debts

def get_unpaid_debts():
    conn = sqlite3.connect(DB_NAME)
    try: df = pd.read_sql_query("SELECT id, date, department, customer_name, amount FROM debts WHERE status='Unpaid' AND amount > 0 ORDER BY id DESC", conn)
    except: df = pd.DataFrame()
    conn.close()
    return df

def process_debt_repayment(debt_id, payment_amount, staff_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT amount, customer_name FROM debts WHERE id=?", (debt_id,))
    result = c.fetchone()
    if not result:
        conn.close(); return False, "Debt record not found."
    current_amount, customer = result
    if payment_amount > current_amount:
        conn.close(); return False, f"Error: Payment (₦{payment_amount}) is more than debt (₦{current_amount})."
    new_balance = current_amount - payment_amount
    if new_balance <= 0: c.execute("UPDATE debts SET amount=0, status='Paid' WHERE id=?", (debt_id,))
    else: c.execute("UPDATE debts SET amount=? WHERE id=?", (new_balance, debt_id))
    date_str = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT INTO daily_sales (date, department, gross_revenue, total_expenses, net_cash, submitted_by) VALUES (?, ?, ?, ?, ?, ?)", (date_str, "DEBT_RECOVERY", payment_amount, 0, payment_amount, staff_name))
    conn.commit(); conn.close()
    return True, f"Repayment of ₦{payment_amount:,.2f} recorded for {customer}!"

def get_pos_history(): 
    # Fetch detailed POS history
    return _get_history("pos_records")

def get_fuel_history(): return _get_history("fuel_records")
def get_bakery_history(): return _get_history("bakery_records")
def get_farm_history(): return _get_history("farm_records")

def _get_history(table):
    conn = sqlite3.connect(DB_NAME)
    try: df = pd.read_sql_query(f"SELECT * FROM {table} ORDER BY id DESC LIMIT 50", conn)
    except: df = pd.DataFrame()
    conn.close()
    return df

init_db()