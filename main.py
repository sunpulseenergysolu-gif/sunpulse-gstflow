from src.gst_lookup import lookup_gstin
from src.rate_limiter import check_login_lockout, record_failed_attempt, record_successful_login, get_failed_attempts
from fastapi import Request
# GSTFlow - Backend Server & API Routes
import os
import io
import shutil
import uuid
import json
from typing import Optional, List
from datetime import datetime, date

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query, Response, status
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.db import get_db, init_db, DB_PATH
from src.state_codes import GST_STATES, get_state_name_by_code, get_state_code_from_gstin
from src.number_to_words import number_to_words_inr
from src.gst_engine import calculate_invoice_totals, calculate_net_gst_liability
from src.pdf_engine import generate_invoice_pdf
from src.excel_engine import (
    generate_gstr1_excel,
    generate_gstr3b_excel,
    generate_sales_register_excel,
    generate_purchases_register_excel,
    generate_ca_master_excel,
    generate_ca_zip_package
)
from src.gst_json_engine import (
    generate_gstr1_json,
    generate_gstr3b_json
)
from src.master_storage import (
    save_master_storage,
    auto_restore_from_master_file_if_needed,
    DESKTOP_MASTER_JSON,
    DESKTOP_MASTER_EXCEL,
    LOCAL_MASTER_JSON
)

# Initialize Database & Auto-Recover from Master Storage Vault File
init_db()
try:
    auto_restore_from_master_file_if_needed()
except Exception as e:
    print("Master storage boot check:", e)

# Immediately ensure master storage file exists
try:
    save_master_storage()
except Exception as e:
    print("Master storage initial save:", e)

app = FastAPI(title="GSTFlow - GST Invoicing & ITC Management API", version="2.1.0")


@app.middleware("http")
async def vercel_path_normalizer(request: Request, call_next):
    matched_path = request.headers.get("x-matched-path") or request.headers.get("x-forwarded-uri") or request.headers.get("x-original-uri")
    if matched_path:
        orig_path = matched_path.split("?")[0]
        request.scope["path"] = orig_path
    else:
        path = request.scope.get("path", "")
        for prefix in ["/api/index.py", "/api/index"]:
            if path == prefix:
                request.scope["path"] = "/"
                break
            elif path.startswith(prefix + "/"):
                request.scope["path"] = path[len(prefix):]
                break
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Surrogate-Control"] = "no-store"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.environ.get("VERCEL") == "1" or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    UPLOADS_DIR = "/tmp/uploads"
else:
    UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")

try:
    os.makedirs(UPLOADS_DIR, exist_ok=True)
except Exception:
    pass

try:
    os.makedirs(STATIC_DIR, exist_ok=True)
except Exception:
    pass

if os.path.exists(UPLOADS_DIR):
    app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
if os.path.exists(STATIC_DIR):
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
    sales_person: Optional[str] = 'SUFIYAN SHAIKH'
    party_email: Optional[str] = ''
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

class CreatePurchaseBillSchema(BaseModel):
    bill_number: Optional[str] = None
    bill_date: str
    due_date: Optional[str] = None
    vendor_id: Optional[int] = None
    vendor_name: str
    vendor_gstin: Optional[str] = ""
    supply_type: Optional[str] = "B2B"
    place_of_supply: Optional[str] = ""
    is_interstate: Optional[bool] = False
    taxable_amount: Optional[float] = 0.0
    gst_rate: Optional[float] = 18.0
    itc_eligibility: Optional[str] = "ELIGIBLE"
    payment_status: Optional[str] = "UNPAID"
    amount_paid: Optional[float] = 0.0
    notes: Optional[str] = ""
    items: Optional[List[InvoiceItemSchema]] = []

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

class LoginSchema(BaseModel):
    username: Optional[str] = ""
    password: Optional[str] = ""
    pin_code: Optional[str] = ""

class ChangeCredentialsSchema(BaseModel):
    current_password: str
    new_username: Optional[str] = None
    new_password: Optional[str] = None
    new_pin: Optional[str] = None

class AdminManageCaSchema(BaseModel):
    admin_password: str
    ca_username: Optional[str] = "ca_audit"
    ca_password: Optional[str] = None
    ca_pin: Optional[str] = None

# ----------------- PERIOD FILTERING HELPERS -----------------

def parse_universal_date(dt_str: str):
    if not dt_str:
        return None, None, None, "", "", ""
    s = str(dt_str).strip().replace("/", "-").replace(".", "-")
    parts = s.split("-")
    if len(parts) >= 3:
        try:
            p0, p1, p2 = int(parts[0]), int(parts[1]), int(parts[2])
            if p0 > 1000:
                y, m, d = p0, p1, p2
            elif p2 > 1000:
                d, m, y = p0, p1, p2
            else:
                y = 2000 + p0 if p0 < 50 else 1900 + p0
                m, d = p1, p2
            
            m_code = str(m).zfill(2)
            fy = f"{y}-{str(y + 1)[2:]}" if m >= 4 else f"{y - 1}-{str(y)[2:]}"
            q = "Q1" if 4 <= m <= 6 else "Q2" if 7 <= m <= 9 else "Q3" if 10 <= m <= 12 else "Q4"
            return y, m, d, fy, m_code, q
        except Exception:
            pass
    return None, None, None, "", "", ""

def filter_records_by_period(
    records: List[dict],
    date_key: str = "invoice_date",
    fy: Optional[str] = None,
    quarter: Optional[str] = None,
    month: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[dict]:
    if not fy and not quarter and not month and not start_date and not end_date:
        return records

    filtered = []
    for r in records:
        dt_str = str(r.get(date_key, "")).strip()
        y, m, d, rec_fy, m_code, rec_q = parse_universal_date(dt_str)

        if not y:
            if (not fy or fy == "ALL") and (not month or month == "ALL") and (not quarter or quarter == "ALL"):
                filtered.append(r)
            continue

        # Financial Year matching
        if fy and fy != "ALL" and rec_fy != fy:
            continue

        # Quarter matching
        if quarter and quarter != "ALL" and rec_q != quarter:
            continue

        # Month matching
        if month and month != "ALL":
            try:
                target_m = str(int(month)).zfill(2)
                if m_code != target_m:
                    continue
            except Exception:
                if m_code != str(month):
                    continue

        filtered.append(r)
    return filtered

def build_period_label(
    fy: Optional[str] = None,
    quarter: Optional[str] = None,
    month: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> str:
    parts = []
    if fy and fy != "ALL":
        parts.append(f"FY {fy}")
    else:
        parts.append("All Financial Years")

    q_labels = {"Q1": "Q1 (Apr - Jun)", "Q2": "Q2 (Jul - Sep)", "Q3": "Q3 (Oct - Dec)", "Q4": "Q4 (Jan - Mar)"}
    m_labels = {
        "01": "January", "02": "February", "03": "March", "04": "April",
        "05": "May", "06": "June", "07": "July", "08": "August",
        "09": "September", "10": "October", "11": "November", "12": "December",
        "1": "January", "2": "February", "3": "March", "4": "April",
        "5": "May", "6": "June", "7": "July", "8": "August",
        "9": "September"
    }

    if quarter and quarter != "ALL":
        parts.append(q_labels.get(quarter, quarter))
    elif month and month != "ALL":
        parts.append(m_labels.get(str(month).zfill(2), f"Month {month}"))
    elif start_date or end_date:
        parts.append(f"({start_date or 'Start'} to {end_date or 'End'})")

    return " • ".join(parts)

# ----------------- ROOT & DASHBOARD -----------------

@app.get("/", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>GSTFlow App is running.</h1>"

@app.get("/api/state-codes")
def get_state_codes():
    return {"states": GST_STATES}

@app.get("/api/gst/lookup/{gstin}")
def api_lookup_gstin(gstin: str):
    return lookup_gstin(gstin, DB_PATH)


@app.get("/api/dashboard")
def get_dashboard_summary(
    fy: Optional[str] = Query(None),
    month: Optional[str] = Query(None)
):
    conn = get_db()
    cursor = conn.cursor()

    # Company details
    cursor.execute("SELECT * FROM company_profile LIMIT 1")
    comp = dict(cursor.fetchone() or {})

    # All Sales Invoices
    cursor.execute("SELECT * FROM sales_invoices ORDER BY invoice_date DESC, id DESC")
    all_sales = [dict(r) for r in cursor.fetchall()]

    # All Purchase Bills
    cursor.execute("SELECT * FROM purchase_bills ORDER BY bill_date DESC, id DESC")
    all_purchases = [dict(r) for r in cursor.fetchall()]

    # Filter by period if specified
    sales_rows = filter_records_by_period(all_sales, "invoice_date", fy=fy, month=month)
    purchase_rows = filter_records_by_period(all_purchases, "bill_date", fy=fy, month=month)

    # Total Sales Metrics for this period
    total_sales_value = sum(float(s["total_amount"] or 0) for s in sales_rows)
    total_taxable_sales = sum(float(s["taxable_amount"] or 0) for s in sales_rows)
    total_sales_count = len(sales_rows)
    total_b2b_sales = sum(float(s["total_amount"] or 0) for s in sales_rows if s["invoice_type"] == "B2B")
    total_b2c_sales = sum(float(s["total_amount"] or 0) for s in sales_rows if s["invoice_type"] == "B2C")
    
    # Receivables & Payables
    receivables = sum(float(s["balance_amount"] or 0) for s in sales_rows)
    payables = sum(float(p["balance_amount"] or 0) for p in purchase_rows)

    # Total Purchases Metrics for this period
    total_purchase_value = sum(float(p["total_amount"] or 0) for p in purchase_rows)
    total_taxable_purchase = sum(float(p["taxable_amount"] or 0) for p in purchase_rows)
    total_purchase_count = len(purchase_rows)

    # ITC and Net Tax Liability Calculation for this period
    tax_analysis = calculate_net_gst_liability(sales_rows, purchase_rows)

    # Complete Transactions List for the active period display
    recent_activity = []
    for s in sales_rows:
        cgst = float(s.get("cgst_amount") or 0)
        sgst = float(s.get("sgst_amount") or 0)
        igst = float(s.get("igst_amount") or 0)
        recent_activity.append({
            "id": s["id"],
            "type": "SALE",
            "number": s.get("invoice_number", ""),
            "party": s.get("party_name", ""),
            "party_gstin": s.get("party_gstin", ""),
            "date": s.get("invoice_date", ""),
            "taxable_amount": float(s.get("taxable_amount") or 0),
            "cgst_amount": cgst,
            "sgst_amount": sgst,
            "igst_amount": igst,
            "tax": cgst + sgst + igst,
            "amount": float(s.get("total_amount") or 0),
            "status": s.get("payment_status", "UNPAID"),
            "tag": s.get("invoice_type", "B2B"),
            "document_file": None
        })
    for p in purchase_rows:
        cgst = float(p.get("cgst_amount") or 0)
        sgst = float(p.get("sgst_amount") or 0)
        igst = float(p.get("igst_amount") or 0)
        recent_activity.append({
            "id": p["id"],
            "type": "PURCHASE",
            "number": p.get("bill_number", ""),
            "party": p.get("vendor_name", ""),
            "party_gstin": p.get("vendor_gstin", ""),
            "date": p.get("bill_date", ""),
            "taxable_amount": float(p.get("taxable_amount") or 0),
            "cgst_amount": cgst,
            "sgst_amount": sgst,
            "igst_amount": igst,
            "tax": cgst + sgst + igst,
            "amount": float(p.get("total_amount") or 0),
            "status": p.get("payment_status", "PAID"),
            "tag": p.get("itc_eligibility", "ELIGIBLE"),
            "document_file": p.get("document_file")
        })
    
    recent_activity.sort(key=lambda x: (str(x["date"] or ""), int(x["id"] or 0)), reverse=True)

    period_label = build_period_label(fy=fy, month=month)

    conn.close()

    return {
        "company": comp,
        "active_period": {
            "fy": fy or "ALL",
            "month": month or "ALL",
            "label": period_label
        },
        "metrics": {
            "total_sales_value": round(total_sales_value, 2),
            "total_taxable_sales": round(total_taxable_sales, 2),
            "total_sales_count": total_sales_count,
            "total_b2b_sales": round(total_b2b_sales, 2),
            "total_b2c_sales": round(total_b2c_sales, 2),
            "total_purchase_value": round(total_purchase_value, 2),
            "total_taxable_purchase": round(total_taxable_purchase, 2),
            "total_purchase_count": total_purchase_count,
            "receivables": round(receivables, 2),
            "payables": round(payables, 2)
        },
        "tax_summary": tax_analysis,
        "recent_activity": recent_activity[:100]
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

    query += " ORDER BY invoice_date DESC, id DESC"
    cursor.execute(query, params)
    invoices = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"invoices": invoices, "sales": invoices}

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

    # Also lookup party addresses if party_id exists
    if invoice_data.get("party_id"):
        cursor.execute("SELECT billing_address, shipping_address FROM parties WHERE id = ?", (invoice_data["party_id"],))
        party_row = cursor.fetchone()
        if party_row:
            invoice_data["party_address"] = party_row["billing_address"]
            invoice_data["shipping_address"] = party_row["shipping_address"]

    conn.close()
    return {"invoice": invoice_data, "items": items, "company": company}


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

    if invoice_data.get("party_id"):
        cursor.execute("SELECT billing_address, shipping_address FROM parties WHERE id = ?", (invoice_data["party_id"],))
        party_row = cursor.fetchone()
        if party_row:
            invoice_data["party_address"] = party_row["billing_address"]
            invoice_data["shipping_address"] = party_row["shipping_address"]

    conn.close()

    pdf_buffer = generate_invoice_pdf(invoice_data, items, company)
    pdf_buffer.seek(0)

    clean_inv_num = str(invoice_data.get("invoice_number", "INV")).replace("/", "_").replace("\\", "_")
    filename = f"Tax_Invoice_{clean_inv_num}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )

DATA_STORE_PATH = os.path.join(os.path.dirname(DB_PATH), "data_store.json")
DESKTOP_STORAGE_JSON = r"C:\Users\One Click Solution\Desktop\GST_BUSINESS_STORAGE_DATA.json"
DESKTOP_STORAGE_DB = r"C:\Users\One Click Solution\Desktop\GST_PERMANENT_DATABASE.db"

def persist_json_mirror():
    try:
        save_master_storage()
    except Exception as e:
        print("JSON Mirror error:", e)
        print("JSON Mirror error:", e)

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

    # Ensure unique invoice number
    cursor.execute("SELECT id FROM sales_invoices WHERE invoice_number = ?", (inv_num,))
    if cursor.fetchone():
        inv_num = f"{inv_num}-{uuid.uuid4().hex[:4].upper()}"

    # Determine Place of Supply & Inter-State
    buyer_state_code = (payload.party_state_code or "27").strip().zfill(2)
    is_interstate = (buyer_state_code != seller_state_code)
    pos = f"{buyer_state_code} - {payload.party_state or 'State'}"

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
        invoice_number, invoice_type, invoice_date, due_date, sales_person, party_id, party_name,
        party_gstin, party_email, party_state, party_state_code, place_of_supply, is_interstate,
        taxable_amount, cgst_amount, sgst_amount, igst_amount, cess_amount,
        round_off, total_amount, amount_in_words, payment_status, amount_paid,
        balance_amount, payment_mode, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        inv_num, payload.invoice_type, payload.invoice_date, payload.due_date, payload.sales_person or 'SUFIYAN SHAIKH', payload.party_id,
        payload.party_name, payload.party_gstin, payload.party_email, payload.party_state, buyer_state_code, pos,
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

    persist_json_mirror()

    return {"message": "Invoice created successfully", "invoice_id": inv_id, "invoice_number": inv_num}

@app.delete("/api/invoices/{inv_id}")
def delete_invoice(inv_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sales_invoice_items WHERE invoice_id = ?", (inv_id,))
    cursor.execute("DELETE FROM payments WHERE reference_type = 'SALES' AND reference_id = ?", (inv_id,))
    cursor.execute("DELETE FROM sales_invoices WHERE id = ?", (inv_id,))
    conn.commit()
    conn.close()
    persist_json_mirror()
    return {"message": "Invoice permanently deleted from database", "id": inv_id}

@app.post("/api/invoices/clear-all")
def clear_all_sales_invoices():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sales_invoice_items")
    cursor.execute("DELETE FROM payments WHERE reference_type = 'SALES'")
    cursor.execute("DELETE FROM sales_invoices")
    conn.commit()
    conn.close()
    persist_json_mirror()
    return {"message": "All sales invoices deleted permanently from database"}


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
    return {"bills": bills, "purchases": bills}

@app.post("/api/purchases/upload")
async def upload_purchase_bill(
    vendor_name: str = Form(...),
    vendor_gstin: Optional[str] = Form(""),
    bill_number: Optional[str] = Form(""),
    bill_date: str = Form(...),
    due_date: Optional[str] = Form(""),
    supply_type: str = Form("B2B"),
    taxable_amount: float = Form(...),
    gst_rate: float = Form(18.0),
    is_interstate: bool = Form(False),
    itc_eligibility: str = Form("ELIGIBLE"),
    payment_status: str = Form("UNPAID"),
    amount_paid: float = Form(0.0),
    notes: Optional[str] = Form(""),
    file: Optional[UploadFile] = File(None)
):
    conn = get_db()
    cursor = conn.cursor()

    # Auto generate bill number if empty
    bill_num = str(bill_number or "").strip()
    if not bill_num:
        cursor.execute("SELECT COUNT(*) FROM purchase_bills")
        count = cursor.fetchone()[0] + 1
        bill_num = f"BILL-{str(count).zfill(3)}"

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
        bill_num, vendor_id, vendor_name, vendor_gstin, bill_date, due_date,
        supply_type, "Purchased Goods/Services", 1 if is_interstate else 0,
        taxable, cgst_amt, sgst_amt, igst_amt, total_amount, itc_eligibility,
        1 if itc_eligibility == 'ELIGIBLE' else 0,
        pay_status, paid, balance, saved_filename, notes
    ))
    bill_id = cursor.lastrowid

    cursor.execute('''
    INSERT INTO purchase_bill_items (bill_id, item_name, hsn_code, quantity, uom, rate, taxable_value, gst_rate, cgst_amount, sgst_amount, igst_amount, total)
    VALUES (?, ?, '', 1, 'Pcs', ?, ?, ?, ?, ?, ?, ?)
    ''', (bill_id, f"Purchase against Bill {bill_num}", taxable, taxable, gst_rate, cgst_amt, sgst_amt, igst_amt, total_amount))

    conn.commit()
    conn.close()

    persist_json_mirror()

    return {"message": "Purchase bill recorded successfully with ITC tracking!", "bill_id": bill_id, "bill_number": bill_num}

@app.post("/api/purchases")
def create_purchase_bill_json(p: CreatePurchaseBillSchema):
    conn = get_db()
    cursor = conn.cursor()

    bill_num = str(p.bill_number or "").strip()
    if not bill_num:
        cursor.execute("SELECT COUNT(*) FROM purchase_bills")
        count = cursor.fetchone()[0] + 1
        bill_num = f"BILL-{str(count).zfill(3)}"

    taxable = float(p.taxable_amount or 0.0)
    if p.items and len(p.items) > 0:
        taxable = sum(float(item.quantity) * float(item.rate) for item in p.items)

    gst_r = float(p.gst_rate or 18.0)
    total_tax = (taxable * gst_r) / 100.0

    if p.is_interstate:
        cgst_amt = 0.0
        sgst_amt = 0.0
        igst_amt = round(total_tax, 2)
    else:
        cgst_amt = round(total_tax / 2.0, 2)
        sgst_amt = round(total_tax / 2.0, 2)
        igst_amt = 0.0

    total_amount = round(taxable + cgst_amt + sgst_amt + igst_amt, 2)
    paid = float(p.amount_paid or 0.0)
    if paid >= total_amount:
        pay_status = "PAID"
        balance = 0.0
    elif paid > 0:
        pay_status = "PARTIAL"
        balance = round(total_amount - paid, 2)
    else:
        pay_status = p.payment_status or "UNPAID"
        balance = total_amount

    cursor.execute('''
    INSERT INTO purchase_bills (
        bill_number, vendor_id, vendor_name, vendor_gstin, bill_date, due_date,
        supply_type, place_of_supply, is_interstate, taxable_amount, cgst_amount,
        sgst_amount, igst_amount, cess_amount, total_amount, itc_eligibility,
        payment_status, amount_paid, balance_amount, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        bill_num, p.vendor_id, p.vendor_name, p.vendor_gstin, p.bill_date, p.due_date,
        p.supply_type or 'B2B', p.place_of_supply, 1 if p.is_interstate else 0,
        taxable, cgst_amt, sgst_amt, igst_amt, 0.0, total_amount,
        p.itc_eligibility or 'ELIGIBLE', pay_status, paid, balance, p.notes
    ))
    bill_id = cursor.lastrowid

    if p.items:
        for it in p.items:
            t_val = float(it.quantity) * float(it.rate)
            t_amt = (t_val * float(it.gst_rate)) / 100.0
            tot = t_val + t_amt
            c_amt = 0.0 if p.is_interstate else round(t_amt / 2.0, 2)
            s_amt = 0.0 if p.is_interstate else round(t_amt / 2.0, 2)
            i_amt = round(t_amt, 2) if p.is_interstate else 0.0
            cursor.execute('''
            INSERT INTO purchase_bill_items (bill_id, item_name, hsn_code, quantity, uom, rate, taxable_value, gst_rate, cgst_amount, sgst_amount, igst_amount, total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (bill_id, it.item_name, it.hsn_code, it.quantity, it.uom, it.rate, t_val, it.gst_rate, c_amt, s_amt, i_amt, tot))

    conn.commit()
    conn.close()
    persist_json_mirror()
    return {"message": "Purchase bill recorded successfully!", "bill_id": bill_id, "bill_number": bill_num, "taxable_amount": taxable, "total_amount": total_amount}

@app.get("/api/purchases/{bill_id}")
def get_purchase_bill_detail(bill_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM purchase_bills WHERE id = ?", (bill_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Purchase bill not found")
    bill_data = dict(row)
    cursor.execute("SELECT * FROM purchase_bill_items WHERE bill_id = ?", (bill_id,))
    items = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"bill": bill_data, "items": items}

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
    cursor.execute("DELETE FROM payments WHERE reference_type = 'PURCHASE' AND reference_id = ?", (bill_id,))
    cursor.execute("DELETE FROM purchase_bills WHERE id = ?", (bill_id,))
    conn.commit()
    conn.close()
    persist_json_mirror()
    return {"message": "Purchase bill permanently deleted from database", "id": bill_id}

@app.post("/api/purchases/clear-all")
def clear_all_purchase_bills():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM purchase_bill_items")
    cursor.execute("DELETE FROM payments WHERE reference_type = 'PURCHASE'")
    cursor.execute("DELETE FROM purchase_bills")
    conn.commit()
    conn.close()
    persist_json_mirror()
    return {"message": "All purchase bills deleted permanently from database"}

@app.post("/api/system/reset-all-transactions")
def reset_all_transactions():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sales_invoice_items")
    cursor.execute("DELETE FROM sales_invoices")
    cursor.execute("DELETE FROM purchase_bill_items")
    cursor.execute("DELETE FROM purchase_bills")
    cursor.execute("DELETE FROM payments")
    conn.commit()
    conn.close()
    return {"message": "All sales invoices, purchase bills, and transactions have been permanently cleared from database"}


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

# ----------------- SECURITY & AUTHENTICATION API (RBAC) -----------------

@app.get("/api/auth/status")
def get_auth_status():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, display_name FROM app_users ORDER BY id ASC")
    users = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"auth_enabled": True, "enabled": True, "users": users}

@app.post("/api/auth/login")
def login_auth(payload: LoginSchema, request: Request):
    # 1. Determine client identifier (IP Address)
    client_ip = request.client.host if request.client else "unknown_client"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    
    user_str = (payload.username or "").strip().lower()
    client_id = f"{client_ip}:{user_str}" if user_str else client_ip

    # 2. Check if currently locked out
    is_locked, rem_secs, total_fails = check_login_lockout(client_id)
    if is_locked:
        raise HTTPException(
            status_code=429,
            detail={
                "message": f"Security Lockout Active: Too many incorrect attempts! Please wait {rem_secs}s before trying again.",
                "is_locked": True,
                "lockout_seconds": rem_secs,
                "failed_count": total_fails
            }
        )

    # 3. Authenticate against database
    conn = get_db()
    cursor = conn.cursor()

    user = None
    pin = (payload.pin_code or "").strip()
    pass_str = (payload.password or "").strip()

    if pin:
        cursor.execute("SELECT * FROM app_users WHERE pin_code = ? LIMIT 1", (pin,))
        user = cursor.fetchone()
    elif user_str and pass_str:
        cursor.execute("SELECT * FROM app_users WHERE lower(username) = ? AND password = ? LIMIT 1", (user_str, pass_str))
        user = cursor.fetchone()

    conn.close()

    # 4. Handle Success vs Failure
    if user:
        record_successful_login(client_id)
        record_successful_login(client_ip)
        if user_str:
            record_successful_login(user_str)

        user_dict = dict(user)
        return {
            "success": True,
            "message": f"Welcome, {user_dict['display_name']}!",
            "username": user_dict["username"],
            "role": user_dict["role"], # 'ADMIN' or 'CA'
            "display_name": user_dict["display_name"]
        }

    # Failed attempt: record and calculate progressive lockout
    lock_secs, total_fails = record_failed_attempt(client_id)
    record_failed_attempt(client_ip)
    if user_str:
        record_failed_attempt(user_str)

    if lock_secs > 0:
        raise HTTPException(
            status_code=429,
            detail={
                "message": f"Too many incorrect attempts! Account locked for {lock_secs} seconds.",
                "is_locked": True,
                "lockout_seconds": lock_secs,
                "failed_count": total_fails
            }
        )
    else:
        attempts_left = max(1, 3 - total_fails)
        raise HTTPException(
            status_code=401,
            detail={
                "message": f"Incorrect credentials! {attempts_left} attempt(s) remaining before 30-sec lockout.",
                "is_locked": False,
                "lockout_seconds": 0,
                "failed_count": total_fails
            }
        )

    user = None
    pin = (payload.pin_code or "").strip()
    user_str = (payload.username or "").strip().lower()
    pass_str = (payload.password or "").strip()

    if pin:
        cursor.execute("SELECT * FROM app_users WHERE pin_code = ? LIMIT 1", (pin,))
        user = cursor.fetchone()
    elif user_str and pass_str:
        cursor.execute("SELECT * FROM app_users WHERE lower(username) = ? AND password = ? LIMIT 1", (user_str, pass_str))
        user = cursor.fetchone()

    conn.close()

    if user:
        user_dict = dict(user)
        return {
            "success": True,
            "message": f"Welcome, {user_dict['display_name']}!",
            "username": user_dict["username"],
            "role": user_dict["role"], # 'ADMIN' or 'CA'
            "display_name": user_dict["display_name"]
        }

    raise HTTPException(status_code=401, detail="Invalid username, password or PIN code")

@app.get("/api/auth/ca-credentials-info")
def get_ca_credentials_info():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username, display_name, pin_code FROM app_users WHERE role = 'CA' LIMIT 1")
    ca = cursor.fetchone()
    conn.close()
    if not ca:
        return {"ca_username": "ca_audit", "ca_display_name": "Chartered Accountant / Auditor", "ca_pin": "4321"}
    return {
        "ca_username": ca["username"],
        "ca_display_name": ca["display_name"],
        "ca_pin": ca["pin_code"] or ""
    }

@app.post("/api/auth/change-credentials")
def change_credentials(payload: ChangeCredentialsSchema):
    conn = get_db()
    cursor = conn.cursor()

    # Find the user matching current password
    cursor.execute("SELECT * FROM app_users WHERE password = ? LIMIT 1", (payload.current_password.strip(),))
    user = cursor.fetchone()

    if not user:
        conn.close()
        raise HTTPException(status_code=400, detail="Current password does not match any active user")

    user_dict = dict(user)

    # If CA attempts to change admin credentials, block them
    if user_dict["role"] == "CA":
        conn.close()
        raise HTTPException(status_code=403, detail="CA / Auditor accounts cannot alter security settings. Contact Admin.")

    new_user = (payload.new_username or user_dict["username"]).strip()
    new_pass = (payload.new_password or user_dict["password"]).strip()
    new_pin = (payload.new_pin or user_dict["pin_code"]).strip()

    # Update app_users
    cursor.execute('''
    UPDATE app_users SET
        username = ?,
        password = ?,
        pin_code = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    ''', (new_user, new_pass, new_pin, user_dict["id"]))

    # Also update security_settings table so both tables stay 100% in sync
    try:
        cursor.execute('''
        UPDATE security_settings SET
            username = ?,
            password = ?,
            pin_code = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = 1
        ''', (new_user, new_pass, new_pin))
    except Exception:
        pass

    conn.commit()
    conn.close()

    # Clear any lockout for this user
    record_successful_login(new_user.lower())
    record_successful_login(user_dict["username"].lower())

    return {
        "success": True,
        "message": "Admin security credentials updated successfully! New password & PIN are active immediately.",
        "username": new_user
    }

    # Find the user matching current password
    cursor.execute("SELECT * FROM app_users WHERE password = ? LIMIT 1", (payload.current_password.strip(),))
    user = cursor.fetchone()

    if not user:
        conn.close()
        raise HTTPException(status_code=400, detail="Current password does not match any active user")

    user_dict = dict(user)

    # If CA attempts to change admin credentials, block them
    if user_dict["role"] == "CA":
        conn.close()
        raise HTTPException(status_code=403, detail="CA / Auditor accounts cannot alter security settings. Contact Admin.")

    new_user = (payload.new_username or user_dict["username"]).strip()
    new_pass = (payload.new_password or user_dict["password"]).strip()
    new_pin = (payload.new_pin or user_dict["pin_code"]).strip()

    cursor.execute('''
    UPDATE app_users SET
        username = ?,
        password = ?,
        pin_code = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    ''', (new_user, new_pass, new_pin, user_dict["id"]))

    conn.commit()
    conn.close()

    return {"success": True, "message": "Admin security credentials updated successfully", "username": new_user}

@app.post("/api/auth/manage-ca")
def manage_ca_credentials(payload: AdminManageCaSchema):
    conn = get_db()
    cursor = conn.cursor()

    # 1. Verify Admin Password
    cursor.execute("SELECT * FROM app_users WHERE role = 'ADMIN' AND password = ? LIMIT 1", (payload.admin_password.strip(),))
    admin_user = cursor.fetchone()

    if not admin_user:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid Admin password. Only Admin can configure CA credentials.")

    # 2. Find CA User
    cursor.execute("SELECT * FROM app_users WHERE role = 'CA' LIMIT 1")
    ca_user = cursor.fetchone()

    if not ca_user:
        # Create CA user if not present
        cursor.execute('''
        INSERT INTO app_users (username, password, role, display_name, pin_code)
        VALUES (?, ?, 'CA', 'Chartered Accountant / Auditor', ?)
        ''', (payload.ca_username or 'ca_audit', payload.ca_password or 'ca123', payload.ca_pin or '4321'))
    else:
        ca_dict = dict(ca_user)
        new_ca_user = (payload.ca_username or ca_dict["username"]).strip()
        new_ca_pass = (payload.ca_password or ca_dict["password"]).strip()
        new_ca_pin = (payload.ca_pin or ca_dict["pin_code"]).strip()

        cursor.execute('''
        UPDATE app_users SET
            username = ?,
            password = ?,
            pin_code = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        ''', (new_ca_user, new_ca_pass, new_ca_pin, ca_dict["id"]))

    conn.commit()
    conn.close()

    return {"success": True, "message": "CA / Auditor login credentials updated successfully!"}

# ----------------- REPORTS & EXCEL EXPORT WITH FY/QUARTER/MONTH FILTERS -----------------

@app.get("/api/reports/gstr1/excel")
def export_gstr1(
    fy: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sales_invoices ORDER BY invoice_date ASC")
    all_invoices = [dict(r) for r in cursor.fetchall()]

    invoices = filter_records_by_period(all_invoices, "invoice_date", fy, quarter, month, start_date, end_date)
    inv_ids = [inv["id"] for inv in invoices]

    items = []
    if inv_ids:
        placeholders = ",".join("?" for _ in inv_ids)
        cursor.execute(f"SELECT * FROM sales_invoice_items WHERE invoice_id IN ({placeholders})", inv_ids)
        items = [dict(r) for r in cursor.fetchall()]
    conn.close()

    period_title = build_period_label(fy, quarter, month, start_date, end_date)
    excel_buf = generate_gstr1_excel(invoices, items, period_title)

    filename = f"GSTR1_Sales_{fy or 'ALL'}_{quarter or month or 'Full'}.xlsx"
    return StreamingResponse(
        excel_buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/reports/gstr3b/excel")
def export_gstr3b(
    fy: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sales_invoices")
    all_sales = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM purchase_bills")
    all_purchases = [dict(r) for r in cursor.fetchall()]
    conn.close()

    sales = filter_records_by_period(all_sales, "invoice_date", fy, quarter, month, start_date, end_date)
    purchases = filter_records_by_period(all_purchases, "bill_date", fy, quarter, month, start_date, end_date)

    tax_summary = calculate_net_gst_liability(sales, purchases)
    period_title = build_period_label(fy, quarter, month, start_date, end_date)
    excel_buf = generate_gstr3b_excel(tax_summary, period_title)

    filename = f"GSTR3B_Tax_Summary_{fy or 'ALL'}_{quarter or month or 'Full'}.xlsx"
    return StreamingResponse(
        excel_buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/reports/gstr1/json")
def export_gstr1_json(
    fy: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM company_profile LIMIT 1")
    comp = dict(cursor.fetchone() or {})

    cursor.execute("SELECT * FROM sales_invoices ORDER BY invoice_date ASC")
    all_invoices = [dict(r) for r in cursor.fetchall()]

    invoices = filter_records_by_period(all_invoices, "invoice_date", fy, quarter, month, start_date, end_date)
    inv_ids = [inv["id"] for inv in invoices]

    items = []
    if inv_ids:
        placeholders = ",".join("?" for _ in inv_ids)
        cursor.execute(f"SELECT * FROM sales_invoice_items WHERE invoice_id IN ({placeholders})", inv_ids)
        items = [dict(r) for r in cursor.fetchall()]
    conn.close()

    json_content = generate_gstr1_json(comp, invoices, items, month, fy)
    gstin = comp.get("gstin", "GSTIN")
    filename = f"GSTR1_{gstin}_{month or 'ALL'}_{fy or 'FY'}.json"
    
    return Response(
        content=json_content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/reports/gstr3b/json")
def export_gstr3b_json(
    fy: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM company_profile LIMIT 1")
    comp = dict(cursor.fetchone() or {})

    cursor.execute("SELECT * FROM sales_invoices")
    all_sales = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM purchase_bills")
    all_purchases = [dict(r) for r in cursor.fetchall()]
    conn.close()

    sales = filter_records_by_period(all_sales, "invoice_date", fy, quarter, month, start_date, end_date)
    purchases = filter_records_by_period(all_purchases, "bill_date", fy, quarter, month, start_date, end_date)

    json_content = generate_gstr3b_json(comp, sales, purchases, month, fy)
    gstin = comp.get("gstin", "GSTIN")
    filename = f"GSTR3B_{gstin}_{month or 'ALL'}_{fy or 'FY'}.json"
    
    return Response(
        content=json_content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/reports/sales/excel")
def export_sales_register(
    fy: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sales_invoices ORDER BY invoice_date ASC, id ASC")
    all_invoices = [dict(r) for r in cursor.fetchall()]

    invoices = filter_records_by_period(all_invoices, "invoice_date", fy, quarter, month, start_date, end_date)
    inv_ids = [inv["id"] for inv in invoices]

    items = []
    if inv_ids:
        placeholders = ",".join("?" for _ in inv_ids)
        cursor.execute(f"SELECT * FROM sales_invoice_items WHERE invoice_id IN ({placeholders})", inv_ids)
        items = [dict(r) for r in cursor.fetchall()]
    conn.close()

    period_title = build_period_label(fy, quarter, month, start_date, end_date)
    excel_buf = generate_sales_register_excel(invoices, items, period_title)

    filename = f"Sales_Register_{fy or 'ALL'}_{quarter or month or 'Full'}.xlsx"
    return StreamingResponse(
        excel_buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/reports/purchases/excel")
def export_purchases_register(
    fy: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM purchase_bills ORDER BY bill_date ASC, id ASC")
    all_purchases = [dict(r) for r in cursor.fetchall()]
    conn.close()

    purchases = filter_records_by_period(all_purchases, "bill_date", fy, quarter, month, start_date, end_date)
    period_title = build_period_label(fy, quarter, month, start_date, end_date)
    excel_buf = generate_purchases_register_excel(purchases, period_title)

    filename = f"Purchases_ITC_Register_{fy or 'ALL'}_{quarter or month or 'Full'}.xlsx"
    return StreamingResponse(
        excel_buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/reports/ca-master/excel")
def export_ca_master_excel(
    fy: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM company_profile LIMIT 1")
    comp = dict(cursor.fetchone() or {})

    cursor.execute("SELECT * FROM sales_invoices ORDER BY invoice_date ASC, id ASC")
    all_sales = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM purchase_bills ORDER BY bill_date ASC, id ASC")
    all_purchases = [dict(r) for r in cursor.fetchall()]

    sales = filter_records_by_period(all_sales, "invoice_date", fy, quarter, month, start_date, end_date)
    purchases = filter_records_by_period(all_purchases, "bill_date", fy, quarter, month, start_date, end_date)

    inv_ids = [inv["id"] for inv in sales]
    items = []
    if inv_ids:
        placeholders = ",".join("?" for _ in inv_ids)
        cursor.execute(f"SELECT * FROM sales_invoice_items WHERE invoice_id IN ({placeholders})", inv_ids)
        items = [dict(r) for r in cursor.fetchall()]

    conn.close()

    tax_summary = calculate_net_gst_liability(sales, purchases)
    period_title = build_period_label(fy, quarter, month, start_date, end_date)
    excel_buf = generate_ca_master_excel(comp, sales, items, purchases, tax_summary, period_title)

    filename = f"CA_Monthly_Master_GST_{fy or 'ALL'}_{month or 'Full'}.xlsx"
    return StreamingResponse(
        excel_buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/reports/ca-package/zip")
def export_ca_zip_bundle(
    fy: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM company_profile LIMIT 1")
    comp = dict(cursor.fetchone() or {})

    cursor.execute("SELECT * FROM sales_invoices ORDER BY invoice_date ASC, id ASC")
    all_sales = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM purchase_bills ORDER BY bill_date ASC, id ASC")
    all_purchases = [dict(r) for r in cursor.fetchall()]

    sales = filter_records_by_period(all_sales, "invoice_date", fy, quarter, month, start_date, end_date)
    purchases = filter_records_by_period(all_purchases, "bill_date", fy, quarter, month, start_date, end_date)

    inv_ids = [inv["id"] for inv in sales]
    items = []
    if inv_ids:
        placeholders = ",".join("?" for _ in inv_ids)
        cursor.execute(f"SELECT * FROM sales_invoice_items WHERE invoice_id IN ({placeholders})", inv_ids)
        items = [dict(r) for r in cursor.fetchall()]

    conn.close()

    tax_summary = calculate_net_gst_liability(sales, purchases)
    period_title = build_period_label(fy, quarter, month, start_date, end_date)
    zip_buf = generate_ca_zip_package(comp, sales, items, purchases, tax_summary, period_title)

    filename = f"CA_Monthly_GST_Package_{fy or 'ALL'}_{month or 'All'}.zip"
    return StreamingResponse(
        zip_buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )



# ----------------- SYSTEM BACKUP & RESTORE API -----------------

@app.get("/api/system/backup")
def export_database_backup():
    """Download full sqlite database backup file with timestamp"""
    from src.db import DB_PATH
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="Database file not found")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"SunPulse_GST_Backup_{timestamp}.db"
    
    with open(DB_PATH, "rb") as f:
        content = f.read()
        
    return Response(
        content=content,
        media_type="application/x-sqlite3",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/api/system/restore")
async def restore_database_backup(backup_file: UploadFile = File(...)):
    """Upload and restore database backup file"""
    from src.db import DB_PATH
    if not backup_file.filename.endswith((".db", ".sqlite", ".sqlite3")):
        raise HTTPException(status_code=400, detail="Invalid backup file format. Please upload a .db or .sqlite file.")
    
    content = await backup_file.read()
    if len(content) < 100:
        raise HTTPException(status_code=400, detail="Backup file is corrupted or empty.")
    
    # Save current as safety backup before replacing
    if os.path.exists(DB_PATH):
        safety_path = DB_PATH + ".safety_bak"
        shutil.copy2(DB_PATH, safety_path)
        
    with open(DB_PATH, "wb") as f:
        f.write(content)
        
    return {"success": True, "message": f"Database successfully restored from {backup_file.filename}!"}

@app.get("/api/system/export-json")
def export_database_json():
    """Download full database structured JSON file for 100% portable backup"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sales_invoices ORDER BY id ASC")
    invoices = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM sales_invoice_items ORDER BY id ASC")
    inv_items = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM purchase_bills ORDER BY id ASC")
    purchases = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM parties ORDER BY id ASC")
    parties = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM items ORDER BY id ASC")
    items = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM company_profile LIMIT 1")
    company = dict(cursor.fetchone() or {})
    conn.close()

    full_export = {
        "app": "SunPulse GSTFlow",
        "export_date": datetime.now().isoformat(),
        "company": company,
        "parties": parties,
        "items": items,
        "invoices": invoices,
        "invoice_items": inv_items,
        "purchases": purchases
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"GSTFlow_Permanent_Backup_{timestamp}.json"
    content = json.dumps(full_export, indent=2, default=str)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/api/sync/restore-browser-state")
async def sync_restore_browser_state(request: Request):
    """Synchronize and restore missing records from Browser LocalStorage/IndexedDB Vault into SQLite"""
    try:
        payload = await request.json()
    except Exception:
        return {"status": "error", "message": "Invalid JSON"}
        
    invoices = payload.get("invoices") or []
    purchases = payload.get("purchases") or []
    parties = payload.get("parties") or []
    items = payload.get("items") or []
    
    conn = get_db()
    cursor = conn.cursor()
    
    restored_invoices = 0
    restored_purchases = 0
    restored_parties = 0
    restored_items = 0
    
    # Restore Parties if not existing
    for p in parties:
        p_name = str(p.get("name") or "").strip()
        if not p_name: continue
        cursor.execute("SELECT id FROM parties WHERE name = ?", (p_name,))
        if not cursor.fetchone():
            cursor.execute('''
            INSERT INTO parties (name, type, gstin, pan, phone, email, state, state_code, billing_address, shipping_address, opening_balance, current_balance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                p_name, p.get("type", "CUSTOMER"), p.get("gstin", ""), p.get("pan", ""),
                p.get("phone", ""), p.get("email", ""), p.get("state", "Gujarat"), p.get("state_code", "24"),
                p.get("billing_address", ""), p.get("shipping_address", ""),
                float(p.get("opening_balance") or 0), float(p.get("current_balance") or 0)
            ))
            restored_parties += 1

    # Restore Items if not existing
    for it in items:
        it_name = str(it.get("name") or "").strip()
        if not it_name: continue
        cursor.execute("SELECT id FROM items WHERE name = ?", (it_name,))
        if not cursor.fetchone():
            cursor.execute('''
            INSERT INTO items (name, description, hsn_code, uom, purchase_price, selling_price, gst_rate, cess_rate, stock_quantity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                it_name, it.get("description", ""), it.get("hsn_code", ""), it.get("uom", "Pcs"),
                float(it.get("purchase_price") or 0), float(it.get("selling_price") or 0),
                float(it.get("gst_rate") or 18), float(it.get("cess_rate") or 0),
                float(it.get("stock_quantity") or 0)
            ))
            restored_items += 1

    # Restore Invoices
    for inv in invoices:
        inv_num = str(inv.get("invoice_number") or "").strip()
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
            new_inv_id = cursor.lastrowid
            
            # Restore line items if available
            inv_line_items = inv.get("items") or []
            for it in inv_line_items:
                cursor.execute('''
                INSERT INTO sales_invoice_items (
                    invoice_id, item_id, item_name, hsn_code, quantity, uom, rate,
                    discount_percent, taxable_value, gst_rate, cgst_rate, cgst_amount,
                    sgst_rate, sgst_amount, igst_rate, igst_amount, total
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    new_inv_id, it.get("item_id"), it.get("item_name", "Product Item"),
                    it.get("hsn_code", ""), float(it.get("quantity") or 1), it.get("uom", "Pcs"),
                    float(it.get("rate") or 0), float(it.get("discount_percent") or 0),
                    float(it.get("taxable_value") or 0), float(it.get("gst_rate") or 18),
                    float(it.get("cgst_rate") or 0), float(it.get("cgst_amount") or 0),
                    float(it.get("sgst_rate") or 0), float(it.get("sgst_amount") or 0),
                    float(it.get("igst_rate") or 0), float(it.get("igst_amount") or 0),
                    float(it.get("total") or 0)
                ))
            restored_invoices += 1

    # Restore Purchases
    for pur in purchases:
        bill_num = str(pur.get("bill_number") or "").strip()
        if not bill_num: continue
        cursor.execute("SELECT id FROM purchase_bills WHERE bill_number = ? AND vendor_name = ?", (bill_num, pur.get("vendor_name")))
        if not cursor.fetchone():
            cursor.execute('''
            INSERT INTO purchase_bills (
                bill_number, vendor_id, vendor_name, vendor_gstin, bill_date,
                taxable_amount, gst_rate, cgst_amount, sgst_amount, igst_amount,
                total_amount, is_interstate, itc_eligibility, itc_category,
                payment_status, amount_paid, balance_amount, document_file, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                bill_num, pur.get("vendor_id"), pur.get("vendor_name"), pur.get("vendor_gstin", ""),
                pur.get("bill_date"), float(pur.get("taxable_amount") or 0), float(pur.get("gst_rate") or 18),
                float(pur.get("cgst_amount") or 0), float(pur.get("sgst_amount") or 0), float(pur.get("igst_amount") or 0),
                float(pur.get("total_amount") or 0), 1 if pur.get("is_interstate") else 0,
                pur.get("itc_eligibility", "ELIGIBLE"), pur.get("itc_category", "INPUT_GOODS"),
                pur.get("payment_status", "PAID"), float(pur.get("amount_paid") or 0), float(pur.get("balance_amount") or 0),
                pur.get("document_file", ""), pur.get("notes", "")
            ))
            restored_purchases += 1

    conn.commit()
    conn.close()
    
    persist_json_mirror()
    
    return {
        "status": "success",
        "restored_invoices": restored_invoices,
        "restored_purchases": restored_purchases,
        "restored_parties": restored_parties,
        "restored_items": restored_items
    }

@app.get("/api/system/download-master-json")
def download_master_json():
    save_master_storage()
    file_to_send = DESKTOP_MASTER_JSON if os.path.exists(DESKTOP_MASTER_JSON) else LOCAL_MASTER_JSON
    if not os.path.exists(file_to_send):
        raise HTTPException(status_code=404, detail="Master storage file not found")
    return FileResponse(
        file_to_send,
        media_type="application/json",
        filename="SUNPULSE_MASTER_BUSINESS_VAULT.json"
    )

@app.get("/api/system/download-master-excel")
def download_master_excel():
    save_master_storage()
    if not os.path.exists(DESKTOP_MASTER_EXCEL):
        raise HTTPException(status_code=404, detail="Master Excel ledger not found")
    return FileResponse(
        DESKTOP_MASTER_EXCEL,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="SUNPULSE_ALL_TRANSACTIONS_MASTER.xlsx"
    )
