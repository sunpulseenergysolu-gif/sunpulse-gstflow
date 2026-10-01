import sqlite3
import os

base_dir = r"C:\Users\One Click Solution\.gemini\antigravity\scratch\gst-invoicing-app"
db_path = os.path.join(base_dir, "gst_flow.db")

# Let's remove old DB to re-seed with SunPulse Energy Solutions & Earthwave Technology sample
if os.path.exists(db_path):
    os.remove(db_path)

db_content = """# SQLite Database Layer with Automatic Seeding
import sqlite3
import os
import json
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gst_flow.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Company Profile
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS company_profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        gstin TEXT NOT NULL,
        pan TEXT,
        state TEXT NOT NULL,
        state_code TEXT NOT NULL,
        address TEXT,
        city TEXT,
        pincode TEXT,
        country TEXT DEFAULT 'India',
        phone TEXT,
        email TEXT,
        logo_path TEXT DEFAULT 'sunpulse_logo.jpg',
        bank_name TEXT,
        bank_acc TEXT,
        bank_ifsc TEXT,
        bank_branch TEXT,
        upi_id TEXT,
        invoice_prefix TEXT DEFAULT 'INVOICE/',
        invoice_terms TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Parties (Customers & Vendors)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS parties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL, -- 'CUSTOMER', 'VENDOR', 'BOTH'
        gstin TEXT,
        pan TEXT,
        phone TEXT,
        email TEXT,
        state TEXT NOT NULL,
        state_code TEXT NOT NULL,
        billing_address TEXT,
        shipping_address TEXT,
        opening_balance REAL DEFAULT 0.0,
        current_balance REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Products / Items Master
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        hsn_code TEXT,
        uom TEXT DEFAULT 'Pcs',
        purchase_price REAL DEFAULT 0.0,
        selling_price REAL DEFAULT 0.0,
        gst_rate REAL DEFAULT 18.0,
        cess_rate REAL DEFAULT 0.0,
        stock_quantity REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Sales Invoices (Outward Taxable Supplies)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sales_invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT UNIQUE NOT NULL,
        invoice_type TEXT DEFAULT 'B2B', -- 'B2B', 'B2C', 'EXPORT', 'BILL_OF_SUPPLY'
        invoice_date TEXT NOT NULL,
        due_date TEXT,
        sales_person TEXT DEFAULT 'SUFIYAN SHAIKH',
        party_id INTEGER,
        party_name TEXT NOT NULL,
        party_gstin TEXT,
        party_email TEXT,
        party_state TEXT,
        party_state_code TEXT,
        place_of_supply TEXT,
        is_interstate INTEGER DEFAULT 0,
        taxable_amount REAL DEFAULT 0.0,
        cgst_amount REAL DEFAULT 0.0,
        sgst_amount REAL DEFAULT 0.0,
        igst_amount REAL DEFAULT 0.0,
        cess_amount REAL DEFAULT 0.0,
        discount_amount REAL DEFAULT 0.0,
        round_off REAL DEFAULT 0.0,
        total_amount REAL DEFAULT 0.0,
        amount_in_words TEXT,
        payment_status TEXT DEFAULT 'UNPAID', -- 'PAID', 'PARTIAL', 'UNPAID'
        amount_paid REAL DEFAULT 0.0,
        balance_amount REAL DEFAULT 0.0,
        payment_mode TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (party_id) REFERENCES parties(id)
    )
    ''')

    # Sales Invoice Line Items
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sales_invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        item_id INTEGER,
        item_name TEXT NOT NULL,
        hsn_code TEXT,
        quantity REAL NOT NULL,
        uom TEXT DEFAULT 'Pcs',
        rate REAL NOT NULL,
        discount_percent REAL DEFAULT 0.0,
        taxable_value REAL NOT NULL,
        gst_rate REAL NOT NULL,
        cgst_rate REAL DEFAULT 0.0,
        cgst_amount REAL DEFAULT 0.0,
        sgst_rate REAL DEFAULT 0.0,
        sgst_amount REAL DEFAULT 0.0,
        igst_rate REAL DEFAULT 0.0,
        igst_amount REAL DEFAULT 0.0,
        total REAL NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES sales_invoices(id) ON DELETE CASCADE
    )
    ''')

    # Purchase & Expense Bills (Inward Supplies / ITC)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS purchase_bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_number TEXT NOT NULL,
        vendor_id INTEGER,
        vendor_name TEXT NOT NULL,
        vendor_gstin TEXT,
        bill_date TEXT NOT NULL,
        due_date TEXT,
        supply_type TEXT DEFAULT 'B2B',
        place_of_supply TEXT,
        is_interstate INTEGER DEFAULT 0,
        taxable_amount REAL DEFAULT 0.0,
        cgst_amount REAL DEFAULT 0.0,
        sgst_amount REAL DEFAULT 0.0,
        igst_amount REAL DEFAULT 0.0,
        cess_amount REAL DEFAULT 0.0,
        total_amount REAL DEFAULT 0.0,
        itc_eligibility TEXT DEFAULT 'ELIGIBLE',
        itc_claimed INTEGER DEFAULT 1,
        payment_status TEXT DEFAULT 'UNPAID',
        amount_paid REAL DEFAULT 0.0,
        balance_amount REAL DEFAULT 0.0,
        document_file TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vendor_id) REFERENCES parties(id)
    )
    ''')

    # Purchase Bill Line Items
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS purchase_bill_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_id INTEGER NOT NULL,
        item_name TEXT NOT NULL,
        hsn_code TEXT,
        quantity REAL DEFAULT 1,
        uom TEXT DEFAULT 'Pcs',
        rate REAL NOT NULL,
        taxable_value REAL NOT NULL,
        gst_rate REAL NOT NULL,
        cgst_amount REAL DEFAULT 0.0,
        sgst_amount REAL DEFAULT 0.0,
        igst_amount REAL DEFAULT 0.0,
        total REAL NOT NULL,
        FOREIGN KEY (bill_id) REFERENCES purchase_bills(id) ON DELETE CASCADE
    )
    ''')

    # Payments & Transactions Log
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        reference_type TEXT NOT NULL,
        reference_id INTEGER NOT NULL,
        reference_number TEXT,
        party_name TEXT NOT NULL,
        amount REAL NOT NULL,
        payment_date TEXT NOT NULL,
        payment_mode TEXT DEFAULT 'UPI',
        transaction_ref TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM company_profile")
    if cursor.fetchone()[0] == 0:
        _seed_demo_data(cursor, conn)

    conn.close()

def _seed_demo_data(cursor, conn):
    # 1. Company Profile (SunPulse Energy Solutions)
    cursor.execute('''
    INSERT INTO company_profile (
        name, gstin, pan, state, state_code, address, city, pincode, country, phone, email, logo_path,
        bank_name, bank_acc, bank_ifsc, bank_branch, upi_id, invoice_prefix, invoice_terms
    ) VALUES (
        'SUNPULSE ENERGY SOLUTIONS', '24MVMPS3622M1ZT', 'MVMPS3622M', 'Gujarat', '24',
        'GF 56/4, CHHIPA NI CHALI/JUNI CHALI\\nRAKHIYAL, Ahmedabad', 'AHMEDABAD', '380023', 'India', '+91 9876543210', 'info@sunpulseenergy.com', 'sunpulse_logo.jpg',
        'HDFC Bank Ltd', '50200088997766', 'HDFC0001234', 'Rakhiyal Ahmedabad Branch', 'sunpulse@okhdfcbank', 'INVOICE/',
        '1. Goods once sold will not be taken back without original warranty card.\\n2. Standard OEM manufacturer warranty applies on Solar Panels & Inverters.\\n3. Subject to Ahmedabad Jurisdiction.'
    )
    ''')

    # 2. Parties
    parties_data = [
        ('EARTHWAVE TECHNOLOGY PRIVATE LIMITED', 'CUSTOMER', '24AAGCE1050R2ZI', 'AAGCE1050R', '9825012345', 'kachhadiyahardik124@gmail.com', 'Gujarat', '24', '511, City Center, Science City Road, Ahmedabad, 380060, Gujarat GJ(India)', '511, City Center, Science City Road, Ahmedabad, 380060, Gujarat GJ(India)', 0, 0),
        ('Zenith Infra & Solar Projects', 'CUSTOMER', '07AACFZ5544H1Z2', 'AACFZ5544H', '9811099887', 'billing@zenithsolar.in', 'Delhi', '07', 'Shop 14, Nehru Place, New Delhi', 'Shop 14, Nehru Place, New Delhi', 0, 0),
        ('Adani Solar Module Suppliers', 'VENDOR', '24AAACA1122B1Z3', 'AAACA1122B', '9909012345', 'sales@adanisolar.com', 'Gujarat', '24', 'Adani Port SEZ, Mundra, Kutch, Gujarat', 'Adani Port SEZ, Mundra, Kutch, Gujarat', 0, 0),
        ('Waaree Energies Hardware Hub', 'VENDOR', '27AABCM6677K1Z8', 'AABCM6677K', '9822334455', 'sales@waaree.com', 'Maharashtra', '27', 'Bhiwandi Logistics Hub, Thane', 'Bhiwandi Logistics Hub, Thane', 0, 0)
    ]
    cursor.executemany('''
    INSERT INTO parties (name, type, gstin, pan, phone, email, state, state_code, billing_address, shipping_address, opening_balance, current_balance)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', parties_data)

    # 3. Items
    items_data = [
        ('SUPPLY OF SOLAR ROOFTOP SYSTEM SET', 'Solar Monocrystalline Photovoltaic Module Sets 540Wp Tier-1', '85414300', 'KW', 25738.89, 25738.89, 5.0, 0.0, 50),
        ('INSTALLATION AND COMISSIONING WORK', 'Complete structure fabrication, ACDB/DCDB wiring and Net-metering commissioning', '998719', 'SET', 52066.11, 52066.11, 18.0, 0.0, 20),
        ('On-Grid Solar String Inverter 5kW', 'High efficiency IP65 dual MPPT 3-phase Solar Inverter', '850440', 'Unit', 38000.0, 48000.0, 12.0, 0.0, 15),
        ('Solar DC Armoured Cable 4 sq.mm', '1000V UV resistant solar DC copper wire (100m roll)', '854470', 'Roll', 4200.0, 5800.0, 18.0, 0.0, 40)
    ]
    cursor.executemany('''
    INSERT INTO items (name, description, hsn_code, uom, purchase_price, selling_price, gst_rate, cess_rate, stock_quantity)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', items_data)

    # 4. Exact Sample Invoice (Matching User Image: INVOICE/01)
    # Untaxed Amount: 1,73,553.71 (1,21,487.60 @ 5% + 52,066.11 @ 18%)
    # SGST: 7,723.14 | CGST: 7,723.14 | Total: 1,89,000.00
    cursor.execute('''
    INSERT INTO sales_invoices (
        invoice_number, invoice_type, invoice_date, due_date, sales_person, party_id, party_name,
        party_gstin, party_email, party_state, party_state_code, place_of_supply, is_interstate,
        taxable_amount, cgst_amount, sgst_amount, igst_amount, round_off, total_amount, amount_in_words,
        payment_status, amount_paid, balance_amount, payment_mode, notes
    ) VALUES (
        'INVOICE/01', 'B2B', '2026-08-22', '2026-08-22', 'SUFIYAN SHAIKH', 1, 'EARTHWAVE TECHNOLOGY PRIVATE LIMITED',
        '24AAGCE1050R2ZI', 'kachhadiyahardik124@gmail.com', 'Gujarat', '24', '24 - Gujarat', 0,
        173553.71, 7723.14, 7723.14, 0.0, 0.01, 189000.0,
        'One Lakh Eighty Nine Thousand Rupees Only', 'PAID', 189000.0, 0.0, 'NEFT', 'Solar Rooftop Installation for Ahmedabad Office'
    )
    ''')
    inv1_id = cursor.lastrowid
    
    # Item 1: Supply of Solar Rooftop System Set (4.72 KW @ 25,738.89 = 1,21,487.60 @ 5% GST -> CGST 2.5% = 3037.19, SGST 2.5% = 3037.19)
    cursor.execute('''
    INSERT INTO sales_invoice_items (invoice_id, item_id, item_name, hsn_code, quantity, uom, rate, taxable_value, gst_rate, cgst_rate, cgst_amount, sgst_rate, sgst_amount, total)
    VALUES (?, 1, 'SUPPLY OF SOLAR ROOFTOP SYSTEM SET', '85414300', 4.72, 'KW', 25738.89, 121487.60, 5.0, 2.5, 3037.19, 2.5, 3037.19, 127561.98)
    ''', (inv1_id,))

    # Item 2: Installation and Commissioning Work (1.00 SET @ 52,066.11 = 52,066.11 @ 18% GST -> CGST 9% = 4685.95, SGST 9% = 4685.95)
    cursor.execute('''
    INSERT INTO sales_invoice_items (invoice_id, item_id, item_name, hsn_code, quantity, uom, rate, taxable_value, gst_rate, cgst_rate, cgst_amount, sgst_rate, sgst_amount, total)
    VALUES (?, 2, 'INSTALLATION AND COMISSIONING WORK', '998719', 1.00, 'SET', 52066.11, 52066.11, 18.0, 9.0, 4685.95, 9.0, 4685.95, 61438.01)
    ''', (inv1_id,))

    # 5. Purchase Bills for ITC
    cursor.execute('''
    INSERT INTO purchase_bills (
        bill_number, vendor_id, vendor_name, vendor_gstin, bill_date, due_date, supply_type,
        place_of_supply, is_interstate, taxable_amount, cgst_amount, sgst_amount, igst_amount,
        total_amount, itc_eligibility, itc_claimed, payment_status, amount_paid, balance_amount,
        document_file, notes
    ) VALUES (
        'BILL-ADANI-772', 3, 'Adani Solar Module Suppliers', '24AAACA1122B1Z3', '2026-08-10', '2026-08-25', 'B2B',
        '24 - Gujarat', 0, 98000.0, 2450.0, 2450.0, 0.0,
        102900.0, 'ELIGIBLE', 1, 'PAID', 102900.0, 0.0,
        'sample_bill_deltacloud.pdf', 'Purchase of 540Wp Solar Panels for Earthwave Project'
    )
    ''')

    conn.commit()
"""

with open(os.path.join(base_dir, "src", "db.py"), "w", encoding="utf-8") as f:
    f.write(db_content)

print("Updated db.py successfully!")
