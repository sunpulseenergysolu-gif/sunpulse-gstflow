# =========================================================================
#   SUNPULSE GSTFLOW - 100% PERMANENT SINGLE MASTER STORAGE ENGINE
# =========================================================================
import sqlite3
import json
import os
import shutil
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

DESKTOP_PATH = r"C:\Users\One Click Solution\Desktop"
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DESKTOP_MASTER_JSON = os.path.join(DESKTOP_PATH, "SUNPULSE_MASTER_BUSINESS_VAULT.json")
DESKTOP_MASTER_EXCEL = os.path.join(DESKTOP_PATH, "SUNPULSE_ALL_TRANSACTIONS_MASTER.xlsx")
LOCAL_MASTER_JSON = os.path.join(PROJECT_DIR, "SUNPULSE_MASTER_BUSINESS_VAULT.json")
LOCAL_DATA_STORE = os.path.join(PROJECT_DIR, "data_store.json")

def get_db_connection():
    from src.db import get_db
    return get_db()

def save_master_storage():
    """
    Saves the entire database into the single master storage file on Desktop & Project directory,
    and updates the master Excel ledger with all Sales and Purchase transactions.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM company_profile LIMIT 1")
        company = dict(cursor.fetchone() or {})

        cursor.execute("SELECT * FROM parties ORDER BY id ASC")
        parties = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM items ORDER BY id ASC")
        items = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM sales_invoices ORDER BY invoice_date DESC, id DESC")
        invoices = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM sales_invoice_items ORDER BY id ASC")
        invoice_items = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM purchase_bills ORDER BY bill_date DESC, id DESC")
        purchases = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM payments ORDER BY id ASC")
        payments = [dict(r) for r in cursor.fetchall()]

        conn.close()

        total_sales_amt = sum(float(i.get("total_amount") or 0) for i in invoices)
        total_taxable_sales = sum(float(i.get("taxable_amount") or 0) for i in invoices)
        total_purchase_amt = sum(float(p.get("total_amount") or 0) for p in purchases)
        total_taxable_pur = sum(float(p.get("taxable_amount") or 0) for p in purchases)

        master_payload = {
            "title": "SUNPULSE ENERGY SOLUTIONS - MASTER BUSINESS VAULT",
            "storage_file_version": "3.0",
            "last_saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "statistics": {
                "total_sales_invoices": len(invoices),
                "total_sales_amount": round(total_sales_amt, 2),
                "total_taxable_sales": round(total_taxable_sales, 2),
                "total_purchase_bills": len(purchases),
                "total_purchase_amount": round(total_purchase_amt, 2),
                "total_taxable_purchases": round(total_taxable_pur, 2),
                "total_parties": len(parties),
                "total_items": len(items)
            },
            "company": company,
            "parties": parties,
            "items": items,
            "invoices": invoices,
            "invoice_items": invoice_items,
            "purchases": purchases,
            "payments": payments
        }

        # 1. Save to Desktop Master JSON file
        try:
            if os.path.exists(DESKTOP_PATH):
                with open(DESKTOP_MASTER_JSON, "w", encoding="utf-8") as f_desk:
                    json.dump(master_payload, f_desk, indent=2, default=str)
        except Exception as e:
            pass

        # 2. Save to Project Master JSON file
        try:
            with open(LOCAL_MASTER_JSON, "w", encoding="utf-8") as f_loc:
                json.dump(master_payload, f_loc, indent=2, default=str)
        except Exception as e:
            pass

        # 3. Save to data_store.json
        try:
            with open(LOCAL_DATA_STORE, "w", encoding="utf-8") as f_ds:
                json.dump(master_payload, f_ds, indent=2, default=str)
        except Exception as e:
            pass

        # 4. Generate Master Excel Ledger on Desktop
        try:
            if os.path.exists(DESKTOP_PATH):
                export_master_excel(master_payload)
        except Exception as e:
            pass

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Master Storage File updated successfully ({len(invoices)} Invoices, {len(purchases)} Bills).")
        return True
    except Exception as e:
        print("Error saving master storage:", e)
        return False

def export_master_excel(payload):
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    accent_fill = PatternFill(start_color="0284C7", end_color="0284C7", fill_type="solid")
    green_fill = PatternFill(start_color="059669", end_color="059669", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    # 1. SHEET: Summary Dashboard
    ws_sum = wb.create_sheet(title="Overview & Summary")
    ws_sum.column_dimensions['A'].width = 30
    ws_sum.column_dimensions['B'].width = 35

    ws_sum["A1"] = "SUNPULSE ENERGY SOLUTIONS - MASTER BUSINESS LEDGER"
    ws_sum["A1"].font = Font(name="Arial", size=14, bold=True, color="0284C7")
    ws_sum["A2"] = f"Storage File Generated: {payload.get('last_saved_at')}"
    ws_sum["A2"].font = Font(name="Arial", size=10, italic=True, color="64748B")

    stats = payload.get("statistics", {})
    summary_rows = [
        ("Business Name", payload.get("company", {}).get("name", "SUNPULSE ENERGY SOLUTIONS")),
        ("GSTIN", payload.get("company", {}).get("gstin", "")),
        ("Total Sales Invoices Count", stats.get("total_sales_invoices", 0)),
        ("Total Sales Gross Value (₹)", stats.get("total_sales_amount", 0)),
        ("Total Taxable Sales (₹)", stats.get("total_taxable_sales", 0)),
        ("Total Purchase Bills Count", stats.get("total_purchase_bills", 0)),
        ("Total Purchase Gross Value (₹)", stats.get("total_purchase_amount", 0)),
        ("Total Taxable Purchases (₹)", stats.get("total_taxable_purchases", 0)),
        ("Registered Customers / Vendors", stats.get("total_parties", 0)),
        ("Product / Item Catalog Items", stats.get("total_items", 0)),
    ]

    r_idx = 4
    for label, val in summary_rows:
        c1 = ws_sum.cell(row=r_idx, column=1, value=label)
        c2 = ws_sum.cell(row=r_idx, column=2, value=val)
        c1.font = Font(name="Arial", size=11, bold=True)
        c2.font = Font(name="Arial", size=11)
        c1.border = thin_border
        c2.border = thin_border
        r_idx += 1

    # 2. SHEET: Sales Invoices
    ws_sales = wb.create_sheet(title="Sales Invoices")
    sales_headers = ["Invoice No", "Type", "Date", "Customer Name", "Customer GSTIN", "Place of Supply", "Taxable (₹)", "CGST (₹)", "SGST (₹)", "IGST (₹)", "Total Amount (₹)", "Payment Status", "Amount Paid (₹)"]
    ws_sales.append(sales_headers)
    for col_idx in range(1, len(sales_headers) + 1):
        cell = ws_sales.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = accent_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for inv in payload.get("invoices", []):
        row = [
            inv.get("invoice_number", ""),
            inv.get("invoice_type", "B2B"),
            inv.get("invoice_date", ""),
            inv.get("party_name", ""),
            inv.get("party_gstin", "Unregistered"),
            inv.get("place_of_supply", ""),
            float(inv.get("taxable_amount") or 0),
            float(inv.get("cgst_amount") or 0),
            float(inv.get("sgst_amount") or 0),
            float(inv.get("igst_amount") or 0),
            float(inv.get("total_amount") or 0),
            inv.get("payment_status", "PAID"),
            float(inv.get("amount_paid") or 0)
        ]
        ws_sales.append(row)

    # 3. SHEET: Purchase Bills
    ws_pur = wb.create_sheet(title="Purchase Bills")
    pur_headers = ["Bill No", "Date", "Supplier / Vendor Name", "Supplier GSTIN", "Taxable (₹)", "GST Rate", "CGST (₹)", "SGST (₹)", "IGST (₹)", "Total Amount (₹)", "ITC Eligibility", "Payment Status"]
    ws_pur.append(pur_headers)
    for col_idx in range(1, len(pur_headers) + 1):
        cell = ws_pur.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = green_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for p in payload.get("purchases", []):
        row = [
            p.get("bill_number", ""),
            p.get("bill_date", ""),
            p.get("vendor_name", ""),
            p.get("vendor_gstin", "Unregistered"),
            float(p.get("taxable_amount") or 0),
            f"{p.get('gst_rate', 18)}%",
            float(p.get("cgst_amount") or 0),
            float(p.get("sgst_amount") or 0),
            float(p.get("igst_amount") or 0),
            float(p.get("total_amount") or 0),
            p.get("itc_eligibility", "ELIGIBLE"),
            p.get("payment_status", "PAID")
        ]
        ws_pur.append(row)

    # Auto-fit column widths
    for sheet in [ws_sales, ws_pur]:
        for col in sheet.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or '')
                if len(val_str) > max_len:
                    max_len = len(val_str)
            sheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

    try:
        wb.save(DESKTOP_MASTER_EXCEL)
    except Exception:
        pass

def auto_restore_from_master_file_if_needed():
    """
    On server boot, if database has 0 invoices but Master File exists,
    restore all records from the Master File.
    """
    master_file = None
    if os.path.exists(DESKTOP_MASTER_JSON):
        master_file = DESKTOP_MASTER_JSON
    elif os.path.exists(LOCAL_MASTER_JSON):
        master_file = LOCAL_MASTER_JSON
    elif os.path.exists(LOCAL_DATA_STORE):
        master_file = LOCAL_DATA_STORE

    if not master_file:
        return

    try:
        with open(master_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        invoices = data.get("invoices") or []
        purchases = data.get("purchases") or []
        parties = data.get("parties") or []
        items = data.get("items") or []

        if not invoices and not purchases:
            return

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check existing count
        cursor.execute("SELECT COUNT(*) FROM sales_invoices")
        curr_inv_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM purchase_bills")
        curr_pur_count = cursor.fetchone()[0]

        restored_inv = 0
        restored_pur = 0

        # If database is missing records, restore from master file
        if curr_inv_count == 0 and invoices:
            for inv in invoices:
                inv_num = inv.get("invoice_number")
                if not inv_num: continue
                cursor.execute("SELECT id FROM sales_invoices WHERE invoice_number = ?", (inv_num,))
                if not cursor.fetchone():
                    cursor.execute('''
                    INSERT INTO sales_invoices (
                        invoice_number, invoice_type, invoice_date, due_date, sales_person, party_id, party_name,
                        party_gstin, party_email, party_state, party_state_code, place_of_supply, is_interstate,
                        taxable_amount, cgst_amount, sgst_amount, igst_amount, cess_amount,
                        round_off, total_amount, amount_in_words, payment_status, amount_paid,
                        balance_amount, payment_mode, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        inv_num, inv.get("invoice_type", "B2B"), inv.get("invoice_date"), inv.get("due_date"),
                        inv.get("sales_person", "SUFIYAN SHAIKH"), inv.get("party_id"), inv.get("party_name"),
                        inv.get("party_gstin", ""), inv.get("party_email", ""), inv.get("party_state", "Gujarat"),
                        inv.get("party_state_code", "24"), inv.get("place_of_supply", "24 - Gujarat"),
                        1 if inv.get("is_interstate") else 0, float(inv.get("taxable_amount") or 0),
                        float(inv.get("cgst_amount") or 0), float(inv.get("sgst_amount") or 0),
                        float(inv.get("igst_amount") or 0), float(inv.get("cess_amount") or 0),
                        float(inv.get("round_off") or 0), float(inv.get("total_amount") or 0),
                        inv.get("amount_in_words", ""), inv.get("payment_status", "PAID"),
                        float(inv.get("amount_paid") or 0), float(inv.get("balance_amount") or 0),
                        inv.get("payment_mode", "UPI"), inv.get("notes", "")
                    ))
                    new_id = cursor.lastrowid
                    # Items
                    for it in inv.get("items") or []:
                        cursor.execute('''
                        INSERT INTO sales_invoice_items (
                            invoice_id, item_id, item_name, hsn_code, quantity, uom, rate,
                            discount_percent, taxable_value, gst_rate, cgst_rate, cgst_amount,
                            sgst_rate, sgst_amount, igst_rate, igst_amount, total
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            new_id, it.get("item_id"), it.get("item_name", "Product Item"),
                            it.get("hsn_code", ""), float(it.get("quantity") or 1), it.get("uom", "Pcs"),
                            float(it.get("rate") or 0), float(it.get("discount_percent") or 0),
                            float(it.get("taxable_value") or 0), float(it.get("gst_rate") or 18),
                            float(it.get("cgst_rate") or 0), float(it.get("cgst_amount") or 0),
                            float(it.get("sgst_rate") or 0), float(it.get("sgst_amount") or 0),
                            float(it.get("igst_rate") or 0), float(it.get("igst_amount") or 0),
                            float(it.get("total") or 0)
                        ))
                    restored_inv += 1

        if curr_pur_count == 0 and purchases:
            for pur in purchases:
                bill_num = pur.get("bill_number")
                if not bill_num: continue
                cursor.execute("SELECT id FROM purchase_bills WHERE bill_number = ?", (bill_num,))
                if not cursor.fetchone():
                    cursor.execute('''
                    INSERT INTO purchase_bills (
                        bill_number, vendor_id, vendor_name, vendor_gstin, bill_date, due_date,
                        supply_type, place_of_supply, is_interstate, taxable_amount, cgst_amount,
                        sgst_amount, igst_amount, total_amount, itc_eligibility, itc_claimed,
                        payment_status, amount_paid, balance_amount, document_file, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        bill_num, pur.get("vendor_id"), pur.get("vendor_name"), pur.get("vendor_gstin", ""),
                        pur.get("bill_date"), pur.get("due_date"), pur.get("supply_type", "B2B"),
                        pur.get("place_of_supply", "Purchased Goods/Services"), 1 if pur.get("is_interstate") else 0,
                        float(pur.get("taxable_amount") or 0), float(pur.get("cgst_amount") or 0),
                        float(pur.get("sgst_amount") or 0), float(pur.get("igst_amount") or 0),
                        float(pur.get("total_amount") or 0), pur.get("itc_eligibility", "ELIGIBLE"),
                        1 if pur.get("itc_eligibility") == 'ELIGIBLE' else 0,
                        pur.get("payment_status", "PAID"), float(pur.get("amount_paid") or 0),
                        float(pur.get("balance_amount") or 0), pur.get("document_file", ""),
                        pur.get("notes", "")
                    ))
                    restored_pur += 1

        conn.commit()
        conn.close()
        if restored_inv > 0 or restored_pur > 0:
            print(f"[AUTO-RECOVERY] Restored {restored_inv} invoices & {restored_pur} bills from Master Storage File.")
    except Exception as e:
        print("Auto-restore note:", e)
