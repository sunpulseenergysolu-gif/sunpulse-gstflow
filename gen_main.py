import os

base_dir = r"C:\Users\One Click Solution\.gemini\antigravity\scratch\gst-invoicing-app"

main_py_content = """# GSTFlow - Backend Server & API Routes
import os
import io
import shutil
import uuid
from typing import Optional, List
from datetime import datetime, date

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query, Response, status
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.db import get_db, init_db
from src.state_codes import GST_STATES, get_state_name_by_code, get_state_code_from_gstin
from src.number_to_words import number_to_words_inr
from src.gst_engine import calculate_invoice_totals, calculate_net_gst_liability
from src.pdf_engine import generate_invoice_pdf
from src.excel_engine import generate_gstr1_excel, generate_gstr3b_excel

# Initialize Database
init_db()

app = FastAPI(title="GSTFlow - GST Invoicing & ITC Management API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ----------------- PYDANTIC SCHEMAS -----------------

class InvoiceItemSchema(BaseModel):
    item_id: Optional[int] = None
    item_name: str
    hsn_code: Optional[str] = ""
    quantity: float = 1.0
    uom: str = "Pcs"
    rate: float = 0.0
    discount_percent: float = 0.0
    gst_rate: float = 18.0

class CreateInvoiceSchema(BaseModel):
    invoice_number: Optional[str] = None
    invoice_type: str = "B2B"  # B2B, B2C, BILL_OF_SUPPLY
    invoice_date: str
    due_date: Optional[str] = None
    party_id: Optional[int] = None
    party_name: str
    party_gstin: Optional[str] = ""
    party_address: Optional[str] = ""
    shipping_address: Optional[str] = ""
    party_state: str
    party_state_code: str
    items: List[InvoiceItemSchema]
    payment_status: str = "UNPAID" # PAID, PARTIAL, UNPAID
    amount_paid: float = 0.0
    payment_mode: Optional[str] = "UPI"
    notes: Optional[str] = ""

class PartySchema(BaseModel):
    name: str
    type: str = "CUSTOMER" # CUSTOMER, VENDOR, BOTH
    gstin: Optional[str] = ""
    pan: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    state: str
    state_code: str
    billing_address: Optional[str] = ""
    shipping_address: Optional[str] = ""

class ItemSchema(BaseModel):
    name: str
    description: Optional[str] = ""
    hsn_code: Optional[str] = ""
    uom: str = "Pcs"
    purchase_price: float = 0.0
    selling_price: float = 0.0
    gst_rate: float = 18.0
    stock_quantity: float = 0.0

class CompanyProfileSchema(BaseModel):
    name: str
    gstin: str
    pan: Optional[str] = ""
    state: str
    state_code: str
    address: Optional[str] = ""
    city: Optional[str] = ""
    pincode: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    bank_name: Optional[str] = ""
    bank_acc: Optional[str] = ""
    bank_ifsc: Optional[str] = ""
    bank_branch: Optional[str] = ""
    upi_id: Optional[str] = ""
    invoice_prefix: Optional[str] = "INV-"
    invoice_terms: Optional[str] = ""

# ----------------- ROOT & DASHBOARD -----------------

@app.get("/", response_class=HTMLResponse)
def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>GSTFlow App is running.</h1>"

@app.get("/api/state-codes")
def get_state_codes():
    return {"states": GST_STATES}

@app.get("/api/dashboard")
def get_dashboard_summary():
    conn = get_db()
    cursor = conn.cursor()

    # Company details
    cursor.execute("SELECT * FROM company_profile LIMIT 1")
    comp = dict(cursor.fetchone() or {})

    # Sales Invoices
    cursor.execute("SELECT * FROM sales_invoices ORDER BY invoice_date DESC")
    sales_rows = [dict(r) for r in cursor.fetchall()]

    # Purchase Bills
    cursor.execute("SELECT * FROM purchase_bills ORDER BY bill_date DESC")
    purchase_rows = [dict(r) for r in cursor.fetchall()]

    # Total Sales Metrics
    total_sales_value = sum(s["total_amount"] for s in sales_rows)
    total_sales_count = len(sales_rows)
    total_b2b_sales = sum(s["total_amount"] for s in sales_rows if s["invoice_type"] == "B2B")
    total_b2c_sales = sum(s["total_amount"] for s in sales_rows if s["invoice_type"] == "B2C")
    
    # Receivables & Payables
    receivables = sum(s["balance_amount"] for s in sales_rows)
    payables = sum(p["balance_amount"] for p in purchase_rows)

    # Total Purchases Metrics
    total_purchase_value = sum(p["total_amount"] for p in purchase_rows)
    total_purchase_count = len(purchase_rows)

    # ITC and Net Tax Liability Calculation
    tax_analysis = calculate_net_gst_liability(sales_rows, purchase_rows)

    # Recent Activity (Combined Invoices and Bills)
    recent_activity = []
    for s in sales_rows[:5]:
        recent_activity.append({
            "id": s["id"],
            "type": "SALE",
            "number": s["invoice_number"],
            "party": s["party_name"],
            "date": s["invoice_date"],
            "amount": s["total_amount"],
            "tax": s["cgst_amount"] + s["sgst_amount"] + s["igst_amount"],
            "status": s["payment_status"],
            "tag": s["invoice_type"]
        })
    for p in purchase_rows[:5]:
        recent_activity.append({
            "id": p["id"],
            "type": "PURCHASE",
            "number": p["bill_number"],
            "party": p["vendor_name"],
            "date": p["bill_date"],
            "amount": p["total_amount"],
            "tax": p["cgst_amount"] + p["sgst_amount"] + p["igst_amount"],
            "status": p["payment_status"],
            "tag": p["itc_eligibility"]
        })
    
    recent_activity.sort(key=lambda x: x["date"], reverse=True)

    conn.close()

    return {
        "company": comp,
        "metrics": {
            "total_sales_value": round(total_sales_value, 2),
            "total_sales_count": total_sales_count,
            "total_b2b_sales": round(total_b2b_sales, 2),
            "total_b2c_sales": round(total_b2c_sales, 2),
            "total_purchase_value": round(total_purchase_value, 2),
            "total_purchase_count": total_purchase_count,
            "receivables": round(receivables, 2),
            "payables": round(payables, 2)
        },
        "tax_summary": tax_analysis,
        "recent_activity": recent_activity[:8]
    }

# ----------------- SALES INVOICES API -----------------

@app.get("/api/invoices")
def list_invoices(
    search: Optional[str] = None,
    type_filter: Optional[str] = None,
    status_filter: Optional[str] = None
):
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM sales_invoices WHERE 1=1"
    params = []

    if search:
        query += " AND (invoice_number LIKE ? OR party_name LIKE ? OR party_gstin LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s])

    if type_filter and type_filter != "ALL":
        query += " AND invoice_type = ?"
        params.append(type_filter)

    if status_filter and status_filter != "ALL":
        query += " AND payment_status = ?"
        params.append(status_filter)

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    invoices = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"invoices": invoices}

@app.get("/api/invoices/{inv_id}")
def get_invoice_detail(inv_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sales_invoices WHERE id = ?", (inv_id,))
    inv = cursor.fetchone()
    if not inv:
        conn.close()
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice_data = dict(inv)

    cursor.execute("SELECT * FROM sales_invoice_items WHERE invoice_id = ?", (inv_id,))
    items = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM company_profile LIMIT 1")
    company = dict(cursor.fetchone() or {})

    conn.close()
    return {"invoice": invoice_data, "items": items, "company": company}

@app.post("/api/invoices")
def create_invoice(payload: CreateInvoiceSchema):
    conn = get_db()
    cursor = conn.cursor()

    # Get Company Profile for State Code & Prefix
    cursor.execute("SELECT * FROM company_profile LIMIT 1")
    company = dict(cursor.fetchone() or {})
    seller_state_code = company.get("state_code", "27")

    # Generate Invoice Number if not given
    inv_num = payload.invoice_number
    if not inv_num or not inv_num.strip():
        prefix = company.get("invoice_prefix", "INV-")
        cursor.execute("SELECT COUNT(*) FROM sales_invoices")
        count = cursor.fetchone()[0] + 1
        inv_num = f"{prefix}{str(count).zfill(3)}"

    # Determine Place of Supply & Inter-State
    buyer_state_code = payload.party_state_code.strip().zfill(2)
    is_interstate = (buyer_state_code != seller_state_code)
    pos = f"{buyer_state_code} - {payload.party_state}"

    # Calculate Totals and Taxes
    items_raw = [item.dict() for item in payload.items]
    calculated = calculate_invoice_totals(items_raw, is_interstate)

    amount_words = number_to_words_inr(calculated["total_amount"])

    # Payment Status & Balance
    amt_paid = payload.amount_paid
    total_amt = calculated["total_amount"]
    if amt_paid >= total_amt:
        payment_status = "PAID"
        balance_amt = 0.0
    elif amt_paid > 0:
        payment_status = "PARTIAL"
        balance_amt = round(total_amt - amt_paid, 2)
    else:
        payment_status = payload.payment_status or "UNPAID"
        balance_amt = total_amt

    cursor.execute('''
    INSERT INTO sales_invoices (
        invoice_number, invoice_type, invoice_date, due_date, party_id, party_name,
        party_gstin, party_state, party_state_code, place_of_supply, is_interstate,
        taxable_amount, cgst_amount, sgst_amount, igst_amount, cess_amount,
        round_off, total_amount, amount_in_words, payment_status, amount_paid,
        balance_amount, payment_mode, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        inv_num, payload.invoice_type, payload.invoice_date, payload.due_date, payload.party_id,
        payload.party_name, payload.party_gstin, payload.party_state, buyer_state_code, pos,
        1 if is_interstate else 0, calculated["taxable_amount"], calculated["cgst_amount"],
        calculated["sgst_amount"], calculated["igst_amount"], 0.0, calculated["round_off"],
        calculated["total_amount"], amount_words, payment_status, amt_paid, balance_amt,
        payload.payment_mode, payload.notes
    ))
    inv_id = cursor.lastrowid

    # Insert Items
    for it in calculated["items"]:
        cursor.execute('''
        INSERT INTO sales_invoice_items (
            invoice_id, item_id, item_name, hsn_code, quantity, uom, rate,
            discount_percent, taxable_value, gst_rate, cgst_rate, cgst_amount,
            sgst_rate, sgst_amount, igst_rate, igst_amount, total
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            inv_id, it.get("item_id"), it.get("item_name"), it.get("hsn_code"),
            it.get("quantity"), it.get("uom"), it.get("rate"), it.get("discount_percent", 0),
            it.get("taxable_value"), it.get("gst_rate"), it.get("cgst_rate", 0),
            it.get("cgst_amount", 0), it.get("sgst_rate", 0), it.get("sgst_amount", 0),
            it.get("igst_rate", 0), it.get("igst_amount", 0), it.get("total")
        ))

    # Log Payment if any amount paid
    if amt_paid > 0:
        cursor.execute('''
        INSERT INTO payments (type, reference_type, reference_id, reference_number, party_name, amount, payment_date, payment_mode, notes)
        VALUES ('RECEIVED', 'SALES', ?, ?, ?, ?, ?, ?, 'Initial payment on invoice creation')
        ''', (inv_id, inv_num, payload.party_name, amt_paid, payload.invoice_date, payload.payment_mode))

    conn.commit()
    conn.close()

    return {"message": "Invoice created successfully", "invoice_id": inv_id, "invoice_number": inv_num}

@app.delete("/api/invoices/{inv_id}")
def delete_invoice(inv_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sales_invoice_items WHERE invoice_id = ?", (inv_id,))
    cursor.execute("DELETE FROM sales_invoices WHERE id = ?", (inv_id,))
    cursor.execute("DELETE FROM payments WHERE reference_type = 'SALES' AND reference_id = ?", (inv_id,))
    conn.commit()
    conn.close()
    return {"message": "Invoice deleted successfully"}

@app.get("/api/invoices/{inv_id}/pdf")
def download_invoice_pdf(inv_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sales_invoices WHERE id = ?", (inv_id,))
    inv = cursor.fetchone()
    if not inv:
        conn.close()
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice_data = dict(inv)

    cursor.execute("SELECT * FROM sales_invoice_items WHERE invoice_id = ?", (inv_id,))
    items = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM company_profile LIMIT 1")
    company = dict(cursor.fetchone() or {})

    # Also lookup party addresses if party_id exists
    if invoice_data.get("party_id"):
        cursor.execute("SELECT billing_address, shipping_address FROM parties WHERE id = ?", (invoice_data["party_id"],))
        party_row = cursor.fetchone()
        if party_row:
            invoice_data["party_address"] = party_row["billing_address"]
            invoice_data["shipping_address"] = party_row["shipping_address"]

    conn.close()

    pdf_buffer = generate_invoice_pdf(invoice_data, items, company)
    filename = f"Invoice_{invoice_data.get('invoice_number', 'GST')}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )

# ----------------- PURCHASE & BILL UPLOAD (ITC) API -----------------

@app.get("/api/purchases")
def list_purchases(
    search: Optional[str] = None,
    itc_filter: Optional[str] = None,
    status_filter: Optional[str] = None
):
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM purchase_bills WHERE 1=1"
    params = []

    if search:
        query += " AND (bill_number LIKE ? OR vendor_name LIKE ? OR vendor_gstin LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s])

    if itc_filter and itc_filter != "ALL":
        query += " AND itc_eligibility = ?"
        params.append(itc_filter)

    if status_filter and status_filter != "ALL":
        query += " AND payment_status = ?"
        params.append(status_filter)

    query += " ORDER BY bill_date DESC, id DESC"
    cursor.execute(query, params)
    bills = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"bills": bills}

@app.post("/api/purchases/upload")
async def upload_purchase_bill(
    vendor_name: str = Form(...),
    vendor_gstin: Optional[str] = Form(""),
    bill_number: str = Form(...),
    bill_date: str = Form(...),
    due_date: Optional[str] = Form(""),
    supply_type: str = Form("B2B"),
    taxable_amount: float = Form(...),
    gst_rate: float = Form(18.0),
    is_interstate: bool = Form(False),
    itc_eligibility: str = Form("ELIGIBLE"), # ELIGIBLE, INELIGIBLE_17_5, CAPITAL_GOODS
    payment_status: str = Form("UNPAID"),
    amount_paid: float = Form(0.0),
    notes: Optional[str] = Form(""),
    file: Optional[UploadFile] = File(None)
):
    saved_filename = ""
    if file and file.filename:
        ext = os.path.splitext(file.filename)[1]
        unique_name = f"bill_{uuid.uuid4().hex[:8]}_{file.filename}"
        dest_path = os.path.join(UPLOADS_DIR, unique_name)
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_filename = unique_name

    # Calculate Taxes
    taxable = float(taxable_amount)
    total_tax = (taxable * float(gst_rate)) / 100.0

    if is_interstate:
        cgst_amt = 0.0
        sgst_amt = 0.0
        igst_amt = round(total_tax, 2)
    else:
        cgst_amt = round(total_tax / 2.0, 2)
        sgst_amt = round(total_tax / 2.0, 2)
        igst_amt = 0.0

    total_amount = round(taxable + cgst_amt + sgst_amt + igst_amt, 2)
    
    # Balance
    paid = float(amount_paid)
    if paid >= total_amount:
        pay_status = "PAID"
        balance = 0.0
    elif paid > 0:
        pay_status = "PARTIAL"
        balance = round(total_amount - paid, 2)
    else:
        pay_status = payment_status
        balance = total_amount

    conn = get_db()
    cursor = conn.cursor()

    # Link or find vendor
    vendor_id = None
    if vendor_name:
        cursor.execute("SELECT id FROM parties WHERE name = ? AND type IN ('VENDOR', 'BOTH') LIMIT 1", (vendor_name,))
        v_row = cursor.fetchone()
        if v_row:
            vendor_id = v_row[0]

    cursor.execute('''
    INSERT INTO purchase_bills (
        bill_number, vendor_id, vendor_name, vendor_gstin, bill_date, due_date,
        supply_type, place_of_supply, is_interstate, taxable_amount, cgst_amount,
        sgst_amount, igst_amount, total_amount, itc_eligibility, itc_claimed,
        payment_status, amount_paid, balance_amount, document_file, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        bill_number, vendor_id, vendor_name, vendor_gstin, bill_date, due_date,
        supply_type, "Purchased Goods/Services", 1 if is_interstate else 0,
        taxable, cgst_amt, sgst_amt, igst_amt, total_amount, itc_eligibility,
        1 if itc_eligibility == 'ELIGIBLE' else 0,
        pay_status, paid, balance, saved_filename, notes
    ))
    bill_id = cursor.lastrowid

    # Add single summary line item
    cursor.execute('''
    INSERT INTO purchase_bill_items (bill_id, item_name, hsn_code, quantity, uom, rate, taxable_value, gst_rate, cgst_amount, sgst_amount, igst_amount, total)
    VALUES (?, ?, '', 1, 'Pcs', ?, ?, ?, ?, ?, ?, ?)
    ''', (bill_id, f"Purchase against Bill {bill_number}", taxable, taxable, gst_rate, cgst_amt, sgst_amt, igst_amt, total_amount))

    conn.commit()
    conn.close()

    return {"message": "Purchase bill recorded successfully with ITC tracking!", "bill_id": bill_id}

@app.delete("/api/purchases/{bill_id}")
def delete_purchase_bill(bill_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT document_file FROM purchase_bills WHERE id = ?", (bill_id,))
    row = cursor.fetchone()
    if row and row["document_file"]:
        f_path = os.path.join(UPLOADS_DIR, row["document_file"])
        if os.path.exists(f_path):
            try:
                os.remove(f_path)
            except Exception:
                pass

    cursor.execute("DELETE FROM purchase_bill_items WHERE bill_id = ?", (bill_id,))
    cursor.execute("DELETE FROM purchase_bills WHERE id = ?", (bill_id,))
    conn.commit()
    conn.close()
    return {"message": "Purchase bill removed"}

# ----------------- PARTIES (CUSTOMERS & VENDORS) API -----------------

@app.get("/api/parties")
def list_parties(type_filter: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()
    if type_filter and type_filter != "ALL":
        cursor.execute("SELECT * FROM parties WHERE type = ? OR type = 'BOTH' ORDER BY name ASC", (type_filter,))
    else:
        cursor.execute("SELECT * FROM parties ORDER BY name ASC")
    parties = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"parties": parties}

@app.post("/api/parties")
def create_party(p: PartySchema):
    conn = get_db()
    cursor = conn.cursor()
    state_code = p.state_code.strip().zfill(2)
    cursor.execute('''
    INSERT INTO parties (name, type, gstin, pan, phone, email, state, state_code, billing_address, shipping_address)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (p.name, p.type, p.gstin, p.pan, p.phone, p.email, p.state, state_code, p.billing_address, p.shipping_address or p.billing_address))
    party_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"message": "Party added successfully", "id": party_id}

@app.delete("/api/parties/{party_id}")
def delete_party(party_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM parties WHERE id = ?", (party_id,))
    conn.commit()
    conn.close()
    return {"message": "Party deleted"}

# ----------------- INVENTORY & ITEMS API -----------------

@app.get("/api/items")
def list_items():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items ORDER BY name ASC")
    items = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"items": items}

@app.post("/api/items")
def create_item(it: ItemSchema):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO items (name, description, hsn_code, uom, purchase_price, selling_price, gst_rate, stock_quantity)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (it.name, it.description, it.hsn_code, it.uom, it.purchase_price, it.selling_price, it.gst_rate, it.stock_quantity))
    item_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"message": "Item added successfully", "id": item_id}

@app.delete("/api/items/{item_id}")
def delete_item(item_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return {"message": "Item deleted"}

# ----------------- SETTINGS & COMPANY PROFILE -----------------

@app.get("/api/settings/company")
def get_company_settings():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM company_profile LIMIT 1")
    comp = dict(cursor.fetchone() or {})
    conn.close()
    return {"company": comp}

@app.post("/api/settings/company")
def update_company_settings(comp: CompanyProfileSchema):
    conn = get_db()
    cursor = conn.cursor()
    state_code = comp.state_code.strip().zfill(2)
    cursor.execute('''
    UPDATE company_profile SET
        name = ?, gstin = ?, pan = ?, state = ?, state_code = ?, address = ?,
        city = ?, pincode = ?, phone = ?, email = ?, bank_name = ?, bank_acc = ?,
        bank_ifsc = ?, bank_branch = ?, upi_id = ?, invoice_prefix = ?, invoice_terms = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = 1
    ''', (
        comp.name, comp.gstin, comp.pan, comp.state, state_code, comp.address,
        comp.city, comp.pincode, comp.phone, comp.email, comp.bank_name, comp.bank_acc,
        comp.bank_ifsc, comp.bank_branch, comp.upi_id, comp.invoice_prefix, comp.invoice_terms
    ))
    conn.commit()
    conn.close()
    return {"message": "Company profile updated successfully"}

# ----------------- REPORTS & EXCEL EXPORT -----------------

@app.get("/api/reports/gstr1/excel")
def export_gstr1():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sales_invoices ORDER BY invoice_date ASC")
    invoices = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM sales_invoice_items")
    items = [dict(r) for r in cursor.fetchall()]
    conn.close()

    excel_buf = generate_gstr1_excel(invoices, items)
    return StreamingResponse(
        excel_buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=GSTR1_Sales_Report.xlsx"}
    )

@app.get("/api/reports/gstr3b/excel")
def export_gstr3b():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sales_invoices")
    sales = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM purchase_bills")
    purchases = [dict(r) for r in cursor.fetchall()]
    conn.close()

    tax_summary = calculate_net_gst_liability(sales, purchases)
    excel_buf = generate_gstr3b_excel(tax_summary)

    return StreamingResponse(
        excel_buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=GSTR3B_Tax_Summary.xlsx"}
    )
"""

with open(os.path.join(base_dir, "main.py"), "w", encoding="utf-8") as f:
    f.write(main_py_content)

print("main.py created successfully!")
