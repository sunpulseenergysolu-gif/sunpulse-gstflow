# GSTR-1, GSTR-3B, Sales Register, Purchase & ITC Register, and CA Master Package Excel Generator
import io
import zipfile
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from typing import List, Dict, Any, Optional

def get_fy_and_quarter(date_str: str):
    if not date_str or "-" not in str(date_str):
        return "", ""
    try:
        parts = str(date_str).split("-")
        y = int(parts[0])
        m = int(parts[1])
        if m >= 4:
            fy = f"FY {y}-{str(y + 1)[2:]}"
        else:
            fy = f"FY {y - 1}-{str(y)[2:]}"
        
        if 4 <= m <= 6:
            q = "Q1 (Apr-Jun)"
        elif 7 <= m <= 9:
            q = "Q2 (Jul-Sep)"
        elif 10 <= m <= 12:
            q = "Q3 (Oct-Dec)"
        else:
            q = "Q4 (Jan-Mar)"
        return fy, q
    except Exception:
        return "", ""

def generate_gstr1_excel(sales_invoices: List[Dict[str, Any]], items_list: List[Dict[str, Any]], period_title: str = "All Periods") -> io.BytesIO:
    wb = openpyxl.Workbook()
    
    # Styles
    hdr_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    hdr_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    bold_font = Font(name="Calibri", size=10, bold=True)
    regular_font = Font(name="Calibri", size=10)

    # Sheet 1: B2B Invoices (Table 4)
    ws_b2b = wb.active
    ws_b2b.title = "GSTR-1 B2B (Table 4)"
    
    b2b_headers = ["GSTIN/UIN of Recipient", "Receiver Name", "Invoice Number", "Invoice Date", "Invoice Value", "Place Of Supply", "Reverse Charge", "Invoice Type", "Tax Rate (%)", "Taxable Value", "Cess Amount"]
    ws_b2b.append(b2b_headers)
    
    for col_num, _ in enumerate(b2b_headers, 1):
        cell = ws_b2b.cell(row=1, column=col_num)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    b2b_invoices = [inv for inv in sales_invoices if inv.get("invoice_type") == "B2B" and inv.get("party_gstin")]
    for inv in b2b_invoices:
        ws_b2b.append([
            inv.get("party_gstin", ""),
            inv.get("party_name", ""),
            inv.get("invoice_number", ""),
            inv.get("invoice_date", ""),
            inv.get("total_amount", 0.0),
            inv.get("place_of_supply", ""),
            "N",
            "Regular",
            18.0,
            inv.get("taxable_amount", 0.0),
            inv.get("cess_amount", 0.0)
        ])

    # Sheet 2: B2CS Small (Table 7)
    ws_b2cs = wb.create_sheet(title="GSTR-1 B2CS (Table 7)")
    b2cs_headers = ["Type", "Place Of Supply", "Rate (%)", "Applicable % of Tax Rate", "Taxable Value", "Cess Amount"]
    ws_b2cs.append(b2cs_headers)
    for col_num, _ in enumerate(b2cs_headers, 1):
        cell = ws_b2cs.cell(row=1, column=col_num)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    b2c_invoices = [inv for inv in sales_invoices if inv.get("invoice_type") == "B2C" or not inv.get("party_gstin")]
    for inv in b2c_invoices:
        ws_b2cs.append([
            "OE",
            inv.get("place_of_supply", ""),
            18.0,
            "",
            inv.get("taxable_amount", 0.0),
            inv.get("cess_amount", 0.0)
        ])

    # Sheet 3: HSN Summary (Table 12)
    ws_hsn = wb.create_sheet(title="HSN Summary (Table 12)")
    hsn_headers = ["HSN Code", "Description", "UQC", "Total Quantity", "Total Value", "Taxable Value", "Integrated Tax (₹)", "Central Tax (₹)", "State Tax (₹)", "Cess (₹)"]
    ws_hsn.append(hsn_headers)
    for col_num, _ in enumerate(hsn_headers, 1):
        cell = ws_hsn.cell(row=1, column=col_num)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Aggregate by HSN
    hsn_map = {}
    for it in items_list:
        hsn = it.get("hsn_code") or "OTHER"
        if hsn not in hsn_map:
            hsn_map[hsn] = {
                "name": it.get("item_name", ""),
                "uom": it.get("uom", "Pcs"),
                "qty": 0.0,
                "taxable": 0.0,
                "cgst": 0.0,
                "sgst": 0.0,
                "igst": 0.0,
                "total": 0.0
            }
        hsn_map[hsn]["qty"] += float(it.get("quantity", 0))
        hsn_map[hsn]["taxable"] += float(it.get("taxable_value", 0))
        hsn_map[hsn]["cgst"] += float(it.get("cgst_amount", 0))
        hsn_map[hsn]["sgst"] += float(it.get("sgst_amount", 0))
        hsn_map[hsn]["igst"] += float(it.get("igst_amount", 0))
        hsn_map[hsn]["total"] += float(it.get("total", 0))

    for hsn, data in hsn_map.items():
        ws_hsn.append([
            hsn,
            data["name"],
            data["uom"],
            data["qty"],
            data["total"],
            data["taxable"],
            data["igst"],
            data["cgst"],
            data["sgst"],
            0.0
        ])

    for sheet in wb.worksheets:
        for col in sheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            sheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

def generate_gstr3b_excel(tax_summary: Dict[str, Any], period_title: str = "All Periods") -> io.BytesIO:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "GSTR-3B Summary"

    hdr_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    hdr_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    section_fill = PatternFill(start_color="E0E7FF", end_color="E0E7FF", fill_type="solid")
    bold_font = Font(name="Calibri", size=10, bold=True)

    ws.append([f"GSTR-3B Tax Liability & Input Tax Credit Return - {period_title}"])
    ws.merge_cells("A1:E1")
    ws.cell(row=1, column=1).font = Font(size=13, bold=True, color="1E3A8A")

    # Table 3.1 Outward Supplies
    ws.append([])
    ws.append(["3.1 Details of Outward Supplies and inward supplies liable to reverse charge"])
    ws.merge_cells("A3:E3")
    ws.cell(row=3, column=1).fill = section_fill
    ws.cell(row=3, column=1).font = bold_font

    headers_31 = ["Nature of Supplies", "Total Taxable Value", "Integrated Tax (IGST)", "Central Tax (CGST)", "State/UT Tax (SGST)"]
    ws.append(headers_31)
    for col_num in range(1, 6):
        ws.cell(row=4, column=col_num).fill = hdr_fill
        ws.cell(row=4, column=col_num).font = hdr_font

    outward = tax_summary.get("output_tax", {})
    ws.append([
        "(a) Outward taxable supplies (other than zero rated, nil rated and exempted)",
        outward.get("total", 0.0),
        outward.get("igst", 0.0),
        outward.get("cgst", 0.0),
        outward.get("sgst", 0.0)
    ])

    # Table 4 Eligible ITC
    ws.append([])
    ws.append(["4. Eligible Input Tax Credit (ITC)"])
    ws.merge_cells("A7:E7")
    ws.cell(row=7, column=1).fill = section_fill
    ws.cell(row=7, column=1).font = bold_font

    headers_4 = ["Details", "Integrated Tax (IGST)", "Central Tax (CGST)", "State/UT Tax (SGST)", "Cess"]
    ws.append(headers_4)
    for col_num in range(1, 6):
        ws.cell(row=8, column=col_num).fill = hdr_fill
        ws.cell(row=8, column=col_num).font = hdr_font

    itc = tax_summary.get("input_tax_credit", {})
    ws.append([
        "(A) ITC Available (whether in full or part) - All other ITC",
        itc.get("igst", 0.0),
        itc.get("cgst", 0.0),
        itc.get("sgst", 0.0),
        0.0
    ])

    # Net Tax Payable Section
    ws.append([])
    ws.append(["5. Net Tax Payable / (Credit Balance)"])
    ws.merge_cells("A11:E11")
    ws.cell(row=11, column=1).fill = section_fill
    ws.cell(row=11, column=1).font = bold_font

    headers_5 = ["Tax Head", "Total Liability (Sales)", "Total ITC Available (Purchases)", "Net Tax Payable", "Closing Credit Balance"]
    ws.append(headers_5)
    for col_num in range(1, 6):
        ws.cell(row=12, column=col_num).fill = hdr_fill
        ws.cell(row=12, column=col_num).font = hdr_font

    net = tax_summary.get("net_payable", {})
    closing = tax_summary.get("closing_credit_balance", {})

    ws.append(["Integrated Tax (IGST)", outward.get("igst", 0), itc.get("igst", 0), net.get("igst", 0), closing.get("igst", 0)])
    ws.append(["Central Tax (CGST)", outward.get("cgst", 0), itc.get("cgst", 0), net.get("cgst", 0), closing.get("cgst", 0)])
    ws.append(["State Tax (SGST)", outward.get("sgst", 0), itc.get("sgst", 0), net.get("sgst", 0), closing.get("sgst", 0)])
    ws.append(["Total", outward.get("total", 0), itc.get("total", 0), net.get("total", 0), closing.get("total", 0)])

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

def generate_sales_register_excel(sales_invoices: List[Dict[str, Any]], items_list: List[Dict[str, Any]], period_title: str = "All Periods") -> io.BytesIO:
    wb = openpyxl.Workbook()
    
    # Header Styles
    hdr_fill = PatternFill(start_color="0284C7", end_color="0284C7", fill_type="solid") # Sky blue
    hdr_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    total_fill = PatternFill(start_color="F0F9FF", end_color="F0F9FF", fill_type="solid")
    bold_font = Font(name="Calibri", size=10, bold=True)
    title_font = Font(name="Calibri", size=13, bold=True, color="0369A1")

    # Sheet 1: Sales Invoices Register
    ws = wb.active
    ws.title = "Sales Invoices Register"

    ws.append([f"Sales Register & Outward Tax Supplies - {period_title}"])
    ws.merge_cells("A1:P1")
    ws.cell(row=1, column=1).font = title_font

    headers = [
        "Invoice #", "Type", "Invoice Date", "FY", "Quarter", 
        "Customer Name", "Customer GSTIN", "Place of Supply", 
        "Taxable Amount (₹)", "CGST (₹)", "SGST (₹)", "IGST (₹)", 
        "Total GST (₹)", "Invoice Total (₹)", "Payment Status", "Balance Due (₹)"
    ]
    ws.append(headers)
    for col_num, _ in enumerate(headers, 1):
        cell = ws.cell(row=2, column=col_num)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    tot_taxable = 0.0
    tot_cgst = 0.0
    tot_sgst = 0.0
    tot_igst = 0.0
    tot_gst = 0.0
    tot_amount = 0.0
    tot_balance = 0.0

    for inv in sales_invoices:
        dt = inv.get("invoice_date", "")
        fy, q = get_fy_and_quarter(dt)
        cgst = float(inv.get("cgst_amount") or 0)
        sgst = float(inv.get("sgst_amount") or 0)
        igst = float(inv.get("igst_amount") or 0)
        gst = cgst + sgst + igst
        taxable = float(inv.get("taxable_amount") or 0)
        total = float(inv.get("total_amount") or 0)
        balance = float(inv.get("balance_amount") or 0)

        tot_taxable += taxable
        tot_cgst += cgst
        tot_sgst += sgst
        tot_igst += igst
        tot_gst += gst
        tot_amount += total
        tot_balance += balance

        ws.append([
            inv.get("invoice_number", ""),
            inv.get("invoice_type", ""),
            dt,
            fy,
            q,
            inv.get("party_name", ""),
            inv.get("party_gstin", "Unregistered"),
            inv.get("place_of_supply", ""),
            taxable,
            cgst,
            sgst,
            igst,
            gst,
            total,
            inv.get("payment_status", "UNPAID"),
            balance
        ])

    # Totals Row
    totals_row = [
        "TOTAL", f"{len(sales_invoices)} Invoices", "", "", "", "", "", "",
        tot_taxable, tot_cgst, tot_sgst, tot_igst, tot_gst, tot_amount, "", tot_balance
    ]
    ws.append(totals_row)
    last_row = ws.max_row
    for col_idx in range(1, len(headers) + 1):
        c = ws.cell(row=last_row, column=col_idx)
        c.font = bold_font
        c.fill = total_fill

    # Sheet 2: Itemized Line Items
    ws_items = wb.create_sheet(title="Item-wise Breakdown")
    item_hdr_fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
    item_headers = ["Invoice #", "Invoice Date", "Item Description", "HSN / SAC", "Quantity", "Unit (UOM)", "Rate (₹)", "GST %", "Taxable (₹)", "CGST (₹)", "SGST (₹)", "IGST (₹)", "Total (₹)"]
    ws_items.append(item_headers)
    for col_num, _ in enumerate(item_headers, 1):
        cell = ws_items.cell(row=1, column=col_num)
        cell.fill = item_hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    inv_date_map = {inv.get("id"): (inv.get("invoice_number"), inv.get("invoice_date")) for inv in sales_invoices}
    for it in items_list:
        inv_info = inv_date_map.get(it.get("invoice_id"), ("", ""))
        ws_items.append([
            inv_info[0],
            inv_info[1],
            it.get("item_name", ""),
            it.get("hsn_code", ""),
            float(it.get("quantity") or 0),
            it.get("uom", "Pcs"),
            float(it.get("rate") or 0),
            float(it.get("gst_rate") or 0),
            float(it.get("taxable_value") or 0),
            float(it.get("cgst_amount") or 0),
            float(it.get("sgst_amount") or 0),
            float(it.get("igst_amount") or 0),
            float(it.get("total") or 0)
        ])

    for sheet in wb.worksheets:
        for col in sheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            sheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

def generate_purchases_register_excel(purchase_bills: List[Dict[str, Any]], period_title: str = "All Periods") -> io.BytesIO:
    wb = openpyxl.Workbook()
    
    # Header Styles
    hdr_fill = PatternFill(start_color="059669", end_color="059669", fill_type="solid") # Emerald green
    hdr_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    total_fill = PatternFill(start_color="ECFDF5", end_color="ECFDF5", fill_type="solid")
    bold_font = Font(name="Calibri", size=10, bold=True)
    title_font = Font(name="Calibri", size=13, bold=True, color="047857")

    ws = wb.active
    ws.title = "Purchase & ITC Register"

    ws.append([f"Purchase Bills & Input Tax Credit (ITC) Register - {period_title}"])
    ws.merge_cells("A1:P1")
    ws.cell(row=1, column=1).font = title_font

    headers = [
        "Bill / Ref #", "Vendor Name", "Vendor GSTIN", "Bill Date", "FY", "Quarter",
        "Place of Supply", "Taxable Purchases (₹)", "Input CGST (₹)", "Input SGST (₹)", 
        "Input IGST (₹)", "Total Input Tax (₹)", "Total Bill Amount (₹)", 
        "ITC Eligibility", "Payment Status", "Balance Due (₹)"
    ]
    ws.append(headers)
    for col_num, _ in enumerate(headers, 1):
        cell = ws.cell(row=2, column=col_num)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    tot_taxable = 0.0
    tot_cgst = 0.0
    tot_sgst = 0.0
    tot_igst = 0.0
    tot_gst = 0.0
    tot_amount = 0.0
    tot_balance = 0.0
    tot_eligible_itc = 0.0
    tot_blocked_itc = 0.0

    for b in purchase_bills:
        dt = b.get("bill_date", "")
        fy, q = get_fy_and_quarter(dt)
        cgst = float(b.get("cgst_amount") or 0)
        sgst = float(b.get("sgst_amount") or 0)
        igst = float(b.get("igst_amount") or 0)
        gst = cgst + sgst + igst
        taxable = float(b.get("taxable_amount") or 0)
        total = float(b.get("total_amount") or 0)
        balance = float(b.get("balance_amount") or 0)
        itc_status = b.get("itc_eligibility", "ELIGIBLE")

        tot_taxable += taxable
        tot_cgst += cgst
        tot_sgst += sgst
        tot_igst += igst
        tot_gst += gst
        tot_amount += total
        tot_balance += balance

        if itc_status == "ELIGIBLE":
            tot_eligible_itc += gst
            itc_label = "🟢 Eligible (Sec 16)"
        else:
            tot_blocked_itc += gst
            itc_label = "🔴 Blocked (Sec 17(5))"

        ws.append([
            b.get("bill_number", ""),
            b.get("vendor_name", ""),
            b.get("vendor_gstin", "Unregistered"),
            dt,
            fy,
            q,
            b.get("place_of_supply", ""),
            taxable,
            cgst,
            sgst,
            igst,
            gst,
            total,
            itc_label,
            b.get("payment_status", "UNPAID"),
            balance
        ])

    # Totals Row
    totals_row = [
        "TOTAL", f"{len(purchase_bills)} Bills", "", "", "", "", "",
        tot_taxable, tot_cgst, tot_sgst, tot_igst, tot_gst, tot_amount,
        f"Eligible: ₹{tot_eligible_itc:.2f} | Blocked: ₹{tot_blocked_itc:.2f}",
        "", tot_balance
    ]
    ws.append(totals_row)
    last_row = ws.max_row
    for col_idx in range(1, len(headers) + 1):
        c = ws.cell(row=last_row, column=col_idx)
        c.font = bold_font
        c.fill = total_fill

    for sheet in wb.worksheets:
        for col in sheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            sheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

def generate_ca_master_excel(
    company: Dict[str, Any],
    sales_invoices: List[Dict[str, Any]],
    sales_items: List[Dict[str, Any]],
    purchase_bills: List[Dict[str, Any]],
    tax_summary: Dict[str, Any],
    period_title: str = "All Periods"
) -> io.BytesIO:
    wb = openpyxl.Workbook()

    # Style definitions
    hdr_navy = PatternFill(start_color="002B66", end_color="002B66", fill_type="solid")
    hdr_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    section_fill = PatternFill(start_color="E0E7FF", end_color="E0E7FF", fill_type="solid")
    accent_green = PatternFill(start_color="059669", end_color="059669", fill_type="solid")
    accent_sky = PatternFill(start_color="0284C7", end_color="0284C7", fill_type="solid")
    bold_font = Font(name="Calibri", size=10, bold=True)
    big_title = Font(name="Calibri", size=14, bold=True, color="002B66")
    sub_title = Font(name="Calibri", size=11, bold=True, color="334155")

    # ================= SHEET 1: CA TAX COMPUTATION & COMPLIANCE SUMMARY =================
    ws1 = wb.active
    ws1.title = "CA Tax Computation"

    ws1.append([f"MONTHLY GST TAX COMPUTATION & AUDIT SUMMARY"])
    ws1.merge_cells("A1:F1")
    ws1.cell(row=1, column=1).font = big_title

    ws1.append([f"Business: {company.get('name', 'SUNPULSE ENERGY SOLUTIONS')} | GSTIN: {company.get('gstin', '24MVMPS3622M1ZT')} | Period: {period_title}"])
    ws1.merge_cells("A2:F2")
    ws1.cell(row=2, column=1).font = sub_title

    ws1.append([])

    # SECTION 1: OUTWARD SUPPLIES (TURNOVER)
    ws1.append(["1. OUTWARD TAXABLE SUPPLIES (SALES TURNOVER)"])
    ws1.merge_cells("A4:F4")
    ws1.cell(row=4, column=1).fill = section_fill
    ws1.cell(row=4, column=1).font = bold_font

    outward_headers = ["Category", "Invoices Count", "Taxable Value (₹)", "CGST (₹)", "SGST (₹)", "IGST (₹)", "Total Tax (₹)", "Gross Total (₹)"]
    ws1.append(outward_headers)
    for c in range(1, 9):
        cell = ws1.cell(row=5, column=c)
        cell.fill = hdr_navy
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center")

    b2b_invs = [s for s in sales_invoices if s.get("invoice_type") == "B2B"]
    b2c_invs = [s for s in sales_invoices if s.get("invoice_type") == "B2C"]

    b2b_taxable = sum(float(s.get("taxable_amount") or 0) for s in b2b_invs)
    b2b_cgst = sum(float(s.get("cgst_amount") or 0) for s in b2b_invs)
    b2b_sgst = sum(float(s.get("sgst_amount") or 0) for s in b2b_invs)
    b2b_igst = sum(float(s.get("igst_amount") or 0) for s in b2b_invs)
    b2b_tax = b2b_cgst + b2b_sgst + b2b_igst
    b2b_gross = sum(float(s.get("total_amount") or 0) for s in b2b_invs)

    b2c_taxable = sum(float(s.get("taxable_amount") or 0) for s in b2c_invs)
    b2c_cgst = sum(float(s.get("cgst_amount") or 0) for s in b2c_invs)
    b2c_sgst = sum(float(s.get("sgst_amount") or 0) for s in b2c_invs)
    b2c_igst = sum(float(s.get("igst_amount") or 0) for s in b2c_invs)
    b2c_tax = b2c_cgst + b2c_sgst + b2c_igst
    b2c_gross = sum(float(s.get("total_amount") or 0) for s in b2c_invs)

    tot_taxable = b2b_taxable + b2c_taxable
    tot_cgst = b2b_cgst + b2c_cgst
    tot_sgst = b2b_sgst + b2c_sgst
    tot_igst = b2b_igst + b2c_igst
    tot_tax = tot_cgst + tot_sgst + tot_igst
    tot_gross = b2b_gross + b2c_gross

    ws1.append(["B2B Supplies (Table 4)", len(b2b_invs), b2b_taxable, b2b_cgst, b2b_sgst, b2b_igst, b2b_tax, b2b_gross])
    ws1.append(["B2C Retail Supplies (Table 7)", len(b2c_invs), b2c_taxable, b2c_cgst, b2c_sgst, b2c_igst, b2c_tax, b2c_gross])
    ws1.append(["TOTAL OUTWARD SUPPLIES", len(sales_invoices), tot_taxable, tot_cgst, tot_sgst, tot_igst, tot_tax, tot_gross])
    for c in range(1, 9):
        ws1.cell(row=8, column=c).font = bold_font

    ws1.append([])

    # SECTION 2: INWARD SUPPLIES & ITC
    ws1.append(["2. INWARD SUPPLIES & INPUT TAX CREDIT (ITC) CLAIM (GSTR-3B TABLE 4)"])
    ws1.merge_cells("A10:F10")
    ws1.cell(row=10, column=1).fill = section_fill
    ws1.cell(row=10, column=1).font = bold_font

    itc_headers = ["ITC Nature", "Bills Count", "Taxable Purchases (₹)", "CGST Credit (₹)", "SGST Credit (₹)", "IGST Credit (₹)", "Total ITC (₹)", "Gross Purchases (₹)"]
    ws1.append(itc_headers)
    for c in range(1, 9):
        cell = ws1.cell(row=11, column=c)
        cell.fill = accent_green
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center")

    elig_bills = [p for p in purchase_bills if p.get("itc_eligibility") == "ELIGIBLE"]
    block_bills = [p for p in purchase_bills if p.get("itc_eligibility") != "ELIGIBLE"]

    el_taxable = sum(float(p.get("taxable_amount") or 0) for p in elig_bills)
    el_cgst = sum(float(p.get("cgst_amount") or 0) for p in elig_bills)
    el_sgst = sum(float(p.get("sgst_amount") or 0) for p in elig_bills)
    el_igst = sum(float(p.get("igst_amount") or 0) for p in elig_bills)
    el_tax = el_cgst + el_sgst + el_igst
    el_gross = sum(float(p.get("total_amount") or 0) for p in elig_bills)

    bl_taxable = sum(float(p.get("taxable_amount") or 0) for p in block_bills)
    bl_cgst = sum(float(p.get("cgst_amount") or 0) for p in block_bills)
    bl_sgst = sum(float(p.get("sgst_amount") or 0) for p in block_bills)
    bl_igst = sum(float(p.get("igst_amount") or 0) for p in block_bills)
    bl_tax = bl_cgst + bl_sgst + bl_igst
    bl_gross = sum(float(p.get("total_amount") or 0) for p in block_bills)

    ws1.append(["(A) Eligible ITC Claimed (Sec 16)", len(elig_bills), el_taxable, el_cgst, el_sgst, el_igst, el_tax, el_gross])
    ws1.append(["(B) Ineligible / Blocked ITC (Sec 17(5))", len(block_bills), bl_taxable, bl_cgst, bl_sgst, bl_igst, bl_tax, bl_gross])
    ws1.append(["TOTAL INWARD PURCHASES", len(purchase_bills), el_taxable + bl_taxable, el_cgst + bl_cgst, el_sgst + bl_sgst, el_igst + bl_igst, el_tax + bl_tax, el_gross + bl_gross])
    for c in range(1, 9):
        ws1.cell(row=14, column=c).font = bold_font

    ws1.append([])

    # SECTION 3: NET TAX COMPUTATION & CHALLAN
    ws1.append(["3. NET TAX COMPUTATION & PAYMENT SETTLEMENT (CHALLAN / CARRY FORWARD)"])
    ws1.merge_cells("A16:F16")
    ws1.cell(row=16, column=1).fill = section_fill
    ws1.cell(row=16, column=1).font = bold_font

    settle_headers = ["Tax Head", "Output Liability (Sales)", "Eligible ITC (Purchases)", "Net Cash Tax Payable (Challan)", "Closing ITC Balance (Carry Forward)"]
    ws1.append(settle_headers)
    for c in range(1, 6):
        cell = ws1.cell(row=17, column=c)
        cell.fill = hdr_navy
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center")

    outward = tax_summary.get("output_tax", {})
    itc = tax_summary.get("input_tax_credit", {})
    net = tax_summary.get("net_payable", {})
    closing = tax_summary.get("closing_credit_balance", {})

    ws1.append(["Integrated Tax (IGST)", outward.get("igst", 0), itc.get("igst", 0), net.get("igst", 0), closing.get("igst", 0)])
    ws1.append(["Central Tax (CGST)", outward.get("cgst", 0), itc.get("cgst", 0), net.get("cgst", 0), closing.get("cgst", 0)])
    ws1.append(["State Tax (SGST)", outward.get("sgst", 0), itc.get("sgst", 0), net.get("sgst", 0), closing.get("sgst", 0)])
    ws1.append(["TOTAL NET GST", outward.get("total", 0), itc.get("total", 0), net.get("total", 0), closing.get("total", 0)])
    for c in range(1, 6):
        ws1.cell(row=21, column=c).font = bold_font

    ws1.append([])
    ws1.append(["4. STATUTORY DUE DATES & FILING CHECKLIST"])
    ws1.merge_cells("A23:E23")
    ws1.cell(row=23, column=1).fill = section_fill
    ws1.cell(row=23, column=1).font = bold_font

    ws1.append(["Return Form", "Frequency", "Standard Due Date", "Action Status"])
    ws1.append(["GSTR-1 (Outward Supplies)", "Monthly", "11th of Next Month", "Data Reconciled & Ready"])
    ws1.append(["GSTR-3B (Tax Payment & ITC)", "Monthly", "20th of Next Month", f"Net Payable: ₹ {net.get('total', 0):,.2f}"])

    # ================= SHEET 2: GSTR-1 OUTWARD SUPPLIES =================
    ws2 = wb.create_sheet(title="GSTR-1 Outward")
    ws2.append(["GSTIN of Recipient", "Party Name", "Invoice No", "Invoice Date", "Type", "Place of Supply", "Taxable Value (₹)", "CGST (₹)", "SGST (₹)", "IGST (₹)", "Total Amount (₹)"])
    for col_idx in range(1, 12):
        cell = ws2.cell(row=1, column=col_idx)
        cell.fill = hdr_navy
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center")

    for s in sales_invoices:
        ws2.append([
            s.get("party_gstin", "Unregistered"),
            s.get("party_name", ""),
            s.get("invoice_number", ""),
            s.get("invoice_date", ""),
            s.get("invoice_type", "B2B"),
            s.get("place_of_supply", ""),
            float(s.get("taxable_amount") or 0),
            float(s.get("cgst_amount") or 0),
            float(s.get("sgst_amount") or 0),
            float(s.get("igst_amount") or 0),
            float(s.get("total_amount") or 0)
        ])

    # ================= SHEET 3: GSTR-3B RETURN (TABLE 3.1 & TABLE 4) =================
    ws3 = wb.create_sheet(title="GSTR-3B Return")
    ws3.append([f"GSTR-3B SUMMARY RETURN - {period_title}"])
    ws3.merge_cells("A1:F1")
    ws3.cell(row=1, column=1).font = big_title

    ws3.append([])
    ws3.append(["Table 3.1: Details of Outward Supplies and inward supplies liable to reverse charge"])
    ws3.merge_cells("A3:F3")
    ws3.cell(row=3, column=1).fill = section_fill
    ws3.cell(row=3, column=1).font = bold_font

    ws3.append(["Nature of Supplies", "Total Taxable Value (₹)", "Integrated Tax (₹)", "Central Tax (₹)", "State/UT Tax (₹)", "Cess (₹)"])
    for c in range(1, 7):
        cell = ws3.cell(row=4, column=c)
        cell.fill = hdr_navy
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center")

    ws3.append([
        "(a) Outward Taxable Supplies (other than zero rated, nil rated and exempted)",
        tot_taxable, outward.get("igst", 0), outward.get("cgst", 0), outward.get("sgst", 0), 0.0
    ])

    ws3.append([])
    ws3.append(["Table 4: Eligible Input Tax Credit (ITC)"])
    ws3.merge_cells("A7:F7")
    ws3.cell(row=7, column=1).fill = section_fill
    ws3.cell(row=7, column=1).font = bold_font

    ws3.append(["Details", "Integrated Tax (₹)", "Central Tax (₹)", "State/UT Tax (₹)", "Cess (₹)", "Total ITC (₹)"])
    for c in range(1, 7):
        cell = ws3.cell(row=8, column=c)
        cell.fill = accent_green
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center")

    ws3.append([
        "(A) ITC Available (All Other ITC - Inward Supplies)",
        itc.get("igst", 0), itc.get("cgst", 0), itc.get("sgst", 0), 0.0, itc.get("total", 0)
    ])
    ws3.append([
        "(B) ITC Ineligible / Blocked (as per Sec 17(5))",
        bl_igst, bl_cgst, bl_sgst, 0.0, bl_tax
    ])
    ws3.append([
        "(C) Net ITC Available (A - B)",
        itc.get("igst", 0), itc.get("cgst", 0), itc.get("sgst", 0), 0.0, itc.get("total", 0)
    ])

    # ================= SHEET 4: SALES REGISTER =================
    ws4 = wb.create_sheet(title="Sales Register")
    s_headers = ["Invoice No", "Party Name", "GSTIN", "Invoice Date", "Period / FY", "Type", "Taxable (₹)", "CGST (₹)", "SGST (₹)", "IGST (₹)", "Total Tax (₹)", "Gross Amount (₹)", "Payment Status"]
    ws4.append(s_headers)
    for c in range(1, len(s_headers) + 1):
        cell = ws4.cell(row=1, column=c)
        cell.fill = hdr_navy
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center")

    for inv in sales_invoices:
        dt = inv.get("invoice_date", "")
        fy, q = get_fy_and_quarter(dt)
        cg = float(inv.get("cgst_amount") or 0)
        sg = float(inv.get("sgst_amount") or 0)
        ig = float(inv.get("igst_amount") or 0)
        ws4.append([
            inv.get("invoice_number", ""),
            inv.get("party_name", ""),
            inv.get("party_gstin", "Unregistered"),
            dt,
            f"{fy} {q}",
            inv.get("invoice_type", "B2B"),
            float(inv.get("taxable_amount") or 0),
            cg, sg, ig, cg + sg + ig,
            float(inv.get("total_amount") or 0),
            inv.get("payment_status", "UNPAID")
        ])

    # ================= SHEET 5: PURCHASE & ITC REGISTER =================
    ws5 = wb.create_sheet(title="Purchase & ITC Register")
    p_headers = ["Bill No", "Vendor Name", "Vendor GSTIN", "Bill Date", "Period / FY", "Taxable (₹)", "CGST (₹)", "SGST (₹)", "IGST (₹)", "Total Tax (₹)", "Gross Amount (₹)", "ITC Status", "Payment Status"]
    ws5.append(p_headers)
    for c in range(1, len(p_headers) + 1):
        cell = ws5.cell(row=1, column=c)
        cell.fill = accent_green
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center")

    for b in purchase_bills:
        dt = b.get("bill_date", "")
        fy, q = get_fy_and_quarter(dt)
        cg = float(b.get("cgst_amount") or 0)
        sg = float(b.get("sgst_amount") or 0)
        ig = float(b.get("igst_amount") or 0)
        itc_tag = "Eligible (Sec 16)" if b.get("itc_eligibility") == "ELIGIBLE" else "Blocked (Sec 17(5))"
        ws5.append([
            b.get("bill_number", ""),
            b.get("vendor_name", ""),
            b.get("vendor_gstin", "Unregistered"),
            dt,
            f"{fy} {q}",
            float(b.get("taxable_amount") or 0),
            cg, sg, ig, cg + sg + ig,
            float(b.get("total_amount") or 0),
            itc_tag,
            b.get("payment_status", "UNPAID")
        ])

    for sheet in wb.worksheets:
        for col in sheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            sheet.column_dimensions[col_letter].width = max(max_len + 3, 14)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

def generate_ca_zip_package(
    company: Dict[str, Any],
    sales_invoices: List[Dict[str, Any]],
    sales_items: List[Dict[str, Any]],
    purchase_bills: List[Dict[str, Any]],
    tax_summary: Dict[str, Any],
    period_title: str = "All Periods"
) -> io.BytesIO:
    from src.gst_json_engine import generate_gstr1_json, generate_gstr3b_json

    zip_buffer = io.BytesIO()

    # Generate individual Excel files
    gstr1_buf = generate_gstr1_excel(sales_invoices, sales_items, period_title)
    gstr3b_buf = generate_gstr3b_excel(tax_summary, period_title)
    sales_buf = generate_sales_register_excel(sales_invoices, sales_items, period_title)
    purchases_buf = generate_purchases_register_excel(purchase_bills, period_title)
    master_buf = generate_ca_master_excel(company, sales_invoices, sales_items, purchase_bills, tax_summary, period_title)

    # Generate Govt GST Portal Direct Upload JSON files
    gstr1_json_str = generate_gstr1_json(company, sales_invoices, sales_items)
    gstr3b_json_str = generate_gstr3b_json(company, sales_invoices, purchase_bills)

    clean_period = period_title.replace(" ", "_").replace("•", "_").replace("/", "-")
    gstin = company.get("gstin", "GSTIN")

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"1_CA_Monthly_Tax_Computation_{clean_period}.xlsx", master_buf.getvalue())
        zf.writestr(f"2_GSTR1_Monthly_Sales_Return_{clean_period}.xlsx", gstr1_buf.getvalue())
        zf.writestr(f"3_GSTR3B_Monthly_Tax_Summary_{clean_period}.xlsx", gstr3b_buf.getvalue())
        zf.writestr(f"4_Sales_Invoices_Register_{clean_period}.xlsx", sales_buf.getvalue())
        zf.writestr(f"5_Purchase_Bills_and_ITC_Register_{clean_period}.xlsx", purchases_buf.getvalue())
        zf.writestr(f"6_GST_PORTAL_DIRECT_UPLOAD_GSTR1_{gstin}_{clean_period}.json", gstr1_json_str.encode("utf-8"))
        zf.writestr(f"7_GST_PORTAL_DIRECT_UPLOAD_GSTR3B_{gstin}_{clean_period}.json", gstr3b_json_str.encode("utf-8"))

    zip_buffer.seek(0)
    return zip_buffer

