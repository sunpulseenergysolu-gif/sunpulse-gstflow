import os

base_dir = r"C:\Users\One Click Solution\.gemini\antigravity\scratch\gst-invoicing-app"
src_dir = os.path.join(base_dir, "src")

# 4. db.py
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
        phone TEXT,
        email TEXT,
        bank_name TEXT,
        bank_acc TEXT,
        bank_ifsc TEXT,
        bank_branch TEXT,
        upi_id TEXT,
        invoice_prefix TEXT DEFAULT 'INV-',
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
        party_id INTEGER,
        party_name TEXT NOT NULL,
        party_gstin TEXT,
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
        supply_type TEXT DEFAULT 'B2B', -- 'B2B', 'B2C', 'EXPENSE', 'IMPORT'
        place_of_supply TEXT,
        is_interstate INTEGER DEFAULT 0,
        taxable_amount REAL DEFAULT 0.0,
        cgst_amount REAL DEFAULT 0.0,
        sgst_amount REAL DEFAULT 0.0,
        igst_amount REAL DEFAULT 0.0,
        cess_amount REAL DEFAULT 0.0,
        total_amount REAL DEFAULT 0.0,
        itc_eligibility TEXT DEFAULT 'ELIGIBLE', -- 'ELIGIBLE', 'INELIGIBLE_17_5', 'CAPITAL_GOODS'
        itc_claimed INTEGER DEFAULT 1,
        payment_status TEXT DEFAULT 'UNPAID', -- 'PAID', 'PARTIAL', 'UNPAID'
        amount_paid REAL DEFAULT 0.0,
        balance_amount REAL DEFAULT 0.0,
        document_file TEXT, -- Filename of uploaded invoice
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
        type TEXT NOT NULL, -- 'RECEIVED' (Customer), 'PAID' (Vendor)
        reference_type TEXT NOT NULL, -- 'SALES', 'PURCHASE'
        reference_id INTEGER NOT NULL,
        reference_number TEXT,
        party_name TEXT NOT NULL,
        amount REAL NOT NULL,
        payment_date TEXT NOT NULL,
        payment_mode TEXT DEFAULT 'UPI', -- 'CASH', 'UPI', 'NEFT', 'CHEQUE'
        transaction_ref TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()

    # Seed Initial Data if empty
    cursor.execute("SELECT COUNT(*) FROM company_profile")
    if cursor.fetchone()[0] == 0:
        _seed_demo_data(cursor, conn)

    conn.close()

def _seed_demo_data(cursor, conn):
    # 1. Company Profile
    cursor.execute('''
    INSERT INTO company_profile (
        name, gstin, pan, state, state_code, address, city, pincode, phone, email,
        bank_name, bank_acc, bank_ifsc, bank_branch, upi_id, invoice_prefix, invoice_terms
    ) VALUES (
        'Bharat Tech & Trading Solutions', '27AABCB1234F1Z5', 'AABCB1234F', 'Maharashtra', '27',
        'Plot No. 42, Tech Park, Andheri East', 'Mumbai', '400069', '+91 9876543210', 'accounts@bharattech.in',
        'HDFC Bank Ltd', '50200012345678', 'HDFC0000123', 'Andheri East Branch', 'bharattech@okhdfcbank', 'INV-2026-',
        '1. Goods once sold will not be taken back without original bill.\n2. Interest @18% p.a. will be charged for delayed payments after due date.\n3. Subject to Mumbai Jurisdiction.'
    )
    ''')

    # 2. Parties (Customers & Vendors)
    parties_data = [
        ('Apex Infotech Pvt Ltd', 'CUSTOMER', '27AAGCA9988G1ZQ', 'AAGCA9988G', '9820011223', 'finance@apexinfo.com', 'Maharashtra', '27', 'B-102, Phoenix Marketcity, Kurla, Mumbai', 'Same as billing', 0, 0),
        ('Zenith Electronics Corp', 'CUSTOMER', '07AACFZ5544H1Z2', 'AACFZ5544H', '9811099887', 'billing@zenithelec.in', 'Delhi', '07', 'Shop 14, Nehru Place, New Delhi', 'Shop 14, Nehru Place, New Delhi', 0, 0),
        ('Shiv Shakti Enterprises', 'CUSTOMER', '', '', '9765432100', 'shivshakti@gmail.com', 'Maharashtra', '27', 'Market Yard, Pune', 'Market Yard, Pune', 0, 0), # B2C
        ('Delta Cloud Hardware Suppliers', 'VENDOR', '24AAACD4433E1Z9', 'AAACD4433E', '9909012345', 'sales@deltacloud.com', 'Gujarat', '24', 'GIDC Phase 2, Vatva, Ahmedabad', 'GIDC Phase 2, Vatva, Ahmedabad', 0, 0),
        ('Metro Office & Stationary Hub', 'VENDOR', '27AABCM6677K1Z8', 'AABCM6677K', '9822334455', 'metrostationery@yahoo.com', 'Maharashtra', '27', 'Fort, Mumbai', 'Fort, Mumbai', 0, 0)
    ]
    cursor.executemany('''
    INSERT INTO parties (name, type, gstin, pan, phone, email, state, state_code, billing_address, shipping_address, opening_balance, current_balance)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', parties_data)

    # 3. Items
    items_data = [
        ('Enterprise Cloud Router AX6000', 'High-speed industrial Wi-Fi router with dual 10G ports', '851762', 'Pcs', 8500.0, 12500.0, 18.0, 0.0, 25),
        ('Optic Fiber Patch Cable 10m', 'Multimode duplex fiber optic cable LC to LC', '854470', 'Pcs', 250.0, 450.0, 18.0, 0.0, 150),
        ('Industrial Server Rack 42U', 'Standard 19 inch network server rack enclosure with cooling fans', '940320', 'Unit', 22000.0, 32000.0, 18.0, 0.0, 8),
        ('Software AMC & Cloud Maintenance', 'Annual maintenance and GST e-invoicing compliance support', '998314', 'Service', 0.0, 15000.0, 18.0, 0.0, 100),
        ('Office Printer Paper A4 (500 sheets)', '75 GSM Premium multi-purpose copier paper', '480256', 'Rim', 220.0, 320.0, 12.0, 0.0, 80)
    ]
    cursor.executemany('''
    INSERT INTO items (name, description, hsn_code, uom, purchase_price, selling_price, gst_rate, cess_rate, stock_quantity)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', items_data)

    # 4. Sample Sales Invoices
    # Invoice 1: Intra-State B2B (Maharashtra -> Maharashtra) CGST 9% + SGST 9%
    cursor.execute('''
    INSERT INTO sales_invoices (
        invoice_number, invoice_type, invoice_date, due_date, party_id, party_name, party_gstin,
        party_state, party_state_code, place_of_supply, is_interstate, taxable_amount,
        cgst_amount, sgst_amount, igst_amount, round_off, total_amount, amount_in_words,
        payment_status, amount_paid, balance_amount, payment_mode, notes
    ) VALUES (
        'INV-2026-001', 'B2B', '2026-09-10', '2026-09-25', 1, 'Apex Infotech Pvt Ltd', '27AAGCA9988G1ZQ',
        'Maharashtra', '27', '27 - Maharashtra', 0, 57000.0, 5130.0, 5130.0, 0.0, 0.0, 67260.0,
        'Sixty Seven Thousand Two Hundred Sixty Rupees Only', 'PAID', 67260.0, 0.0, 'NEFT', 'Delivered via Express Cargo'
    )
    ''')
    inv1_id = cursor.lastrowid
    cursor.execute('''
    INSERT INTO sales_invoice_items (invoice_id, item_id, item_name, hsn_code, quantity, uom, rate, taxable_value, gst_rate, cgst_rate, cgst_amount, sgst_rate, sgst_amount, total)
    VALUES (?, 1, 'Enterprise Cloud Router AX6000', '851762', 4, 'Pcs', 12500.0, 50000.0, 18.0, 9.0, 4500.0, 9.0, 4500.0, 59000.0)
    ''', (inv1_id,))
    cursor.execute('''
    INSERT INTO sales_invoice_items (invoice_id, item_id, item_name, hsn_code, quantity, uom, rate, taxable_value, gst_rate, cgst_rate, cgst_amount, sgst_rate, sgst_amount, total)
    VALUES (?, 4, 'Software AMC & Cloud Maintenance', '998314', 1, 'Service', 7000.0, 7000.0, 18.0, 9.0, 630.0, 9.0, 630.0, 8260.0)
    ''', (inv1_id,))

    # Invoice 2: Inter-State B2B (Maharashtra -> Delhi) IGST 18%
    cursor.execute('''
    INSERT INTO sales_invoices (
        invoice_number, invoice_type, invoice_date, due_date, party_id, party_name, party_gstin,
        party_state, party_state_code, place_of_supply, is_interstate, taxable_amount,
        cgst_amount, sgst_amount, igst_amount, round_off, total_amount, amount_in_words,
        payment_status, amount_paid, balance_amount, notes
    ) VALUES (
        'INV-2026-002', 'B2B', '2026-09-15', '2026-09-30', 2, 'Zenith Electronics Corp', '07AACFZ5544H1Z2',
        'Delhi', '07', '07 - Delhi', 1, 64000.0, 0.0, 0.0, 11520.0, 0.0, 75520.0,
        'Seventy Five Thousand Five Hundred Twenty Rupees Only', 'UNPAID', 0.0, 75520.0, 'Inter-state B2B delivery'
    )
    ''')
    inv2_id = cursor.lastrowid
    cursor.execute('''
    INSERT INTO sales_invoice_items (invoice_id, item_id, item_name, hsn_code, quantity, uom, rate, taxable_value, gst_rate, igst_rate, igst_amount, total)
    VALUES (?, 3, 'Industrial Server Rack 42U', '940320', 2, 'Unit', 32000.0, 64000.0, 18.0, 18.0, 11520.0, 75520.0)
    ''', (inv2_id,))

    # Invoice 3: B2C Retail Sale (Maharashtra)
    cursor.execute('''
    INSERT INTO sales_invoices (
        invoice_number, invoice_type, invoice_date, due_date, party_id, party_name, party_gstin,
        party_state, party_state_code, place_of_supply, is_interstate, taxable_amount,
        cgst_amount, sgst_amount, igst_amount, round_off, total_amount, amount_in_words,
        payment_status, amount_paid, balance_amount, payment_mode
    ) VALUES (
        'INV-2026-003', 'B2C', '2026-09-18', '2026-09-18', 3, 'Shiv Shakti Enterprises', '',
        'Maharashtra', '27', '27 - Maharashtra', 0, 4500.0, 405.0, 405.0, 0.0, 0.0, 5310.0,
        'Five Thousand Three Hundred Ten Rupees Only', 'PAID', 5310.0, 0.0, 'UPI'
    )
    ''')
    inv3_id = cursor.lastrowid
    cursor.execute('''
    INSERT INTO sales_invoice_items (invoice_id, item_id, item_name, hsn_code, quantity, uom, rate, taxable_value, gst_rate, cgst_rate, cgst_amount, sgst_rate, sgst_amount, total)
    VALUES (?, 2, 'Optic Fiber Patch Cable 10m', '854470', 10, 'Pcs', 450.0, 4500.0, 18.0, 9.0, 405.0, 9.0, 405.0, 5310.0)
    ''', (inv3_id,))

    # 5. Sample Purchase & Vendor Bills (For Input Tax Credit - ITC)
    # Bill 1: Inter-State Purchase from Gujarat (Delta Cloud) -> Eligible ITC IGST ?9,180
    cursor.execute('''
    INSERT INTO purchase_bills (
        bill_number, vendor_id, vendor_name, vendor_gstin, bill_date, due_date, supply_type,
        place_of_supply, is_interstate, taxable_amount, cgst_amount, sgst_amount, igst_amount,
        total_amount, itc_eligibility, itc_claimed, payment_status, amount_paid, balance_amount,
        document_file, notes
    ) VALUES (
        'BILL-DC-8841', 4, 'Delta Cloud Hardware Suppliers', '24AAACD4433E1Z9', '2026-09-05', '2026-09-20', 'B2B',
        '27 - Maharashtra', 1, 51000.0, 0.0, 0.0, 9180.0,
        60180.0, 'ELIGIBLE', 1, 'PAID', 60180.0, 0.0,
        'sample_bill_deltacloud.pdf', 'Purchase of 6 units Router AX6000 for resale'
    )
    ''')

    # Bill 2: Intra-State Purchase from Maharashtra (Metro Office) -> Eligible ITC CGST ?768 + SGST ?768
    cursor.execute('''
    INSERT INTO purchase_bills (
        bill_number, vendor_id, vendor_name, vendor_gstin, bill_date, due_date, supply_type,
        place_of_supply, is_interstate, taxable_amount, cgst_amount, sgst_amount, igst_amount,
        total_amount, itc_eligibility, itc_claimed, payment_status, amount_paid, balance_amount,
        document_file, notes
    ) VALUES (
        'METRO-INV-402', 5, 'Metro Office & Stationary Hub', '27AABCM6677K1Z8', '2026-09-12', '2026-09-27', 'B2B',
        '27 - Maharashtra', 0, 12800.0, 768.0, 768.0, 0.0,
        14336.0, 'ELIGIBLE', 1, 'UNPAID', 0.0, 14336.0,
        'sample_bill_metro.pdf', 'Copier Paper and Office Supplies'
    )
    ''')

    # Bill 3: Ineligible Expense (e.g. Food / Staff Catering - Blocked credit u/s 17(5))
    cursor.execute('''
    INSERT INTO purchase_bills (
        bill_number, vendor_id, vendor_name, vendor_gstin, bill_date, due_date, supply_type,
        place_of_supply, is_interstate, taxable_amount, cgst_amount, sgst_amount, igst_amount,
        total_amount, itc_eligibility, itc_claimed, payment_status, amount_paid, balance_amount,
        document_file, notes
    ) VALUES (
        'FOOD-EXP-1102', NULL, 'Royal Caterers & Pantry Services', '27AACCR3322D1ZP', '2026-09-14', '2026-09-14', 'EXPENSE',
        '27 - Maharashtra', 0, 5000.0, 125.0, 125.0, 0.0,
        5250.0, 'INELIGIBLE_17_5', 0, 'PAID', 5250.0, 0.0,
        '', 'Team lunch & refreshment (Blocked ITC under section 17(5))'
    )
    ''')

    # 6. Sample Payments
    cursor.execute('''
    INSERT INTO payments (type, reference_type, reference_id, reference_number, party_name, amount, payment_date, payment_mode, transaction_ref, notes)
    VALUES ('RECEIVED', 'SALES', 1, 'INV-2026-001', 'Apex Infotech Pvt Ltd', 67260.0, '2026-09-10', 'NEFT', 'HDFC00998811', 'Full payment received against INV-001')
    ''')
    cursor.execute('''
    INSERT INTO payments (type, reference_type, reference_id, reference_number, party_name, amount, payment_date, payment_mode, transaction_ref, notes)
    VALUES ('PAID', 'PURCHASE', 1, 'BILL-DC-8841', 'Delta Cloud Hardware Suppliers', 60180.0, '2026-09-08', 'UPI', 'UPI/20260908/332211', 'Paid via Business UPI')
    ''')

    conn.commit()
"""

with open(os.path.join(src_dir, "db.py"), "w", encoding="utf-8") as f:
    f.write(db_content)

print("db.py created successfully!")
