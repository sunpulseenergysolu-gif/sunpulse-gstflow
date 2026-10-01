import os

base_dir = r"C:\Users\One Click Solution\.gemini\antigravity\scratch\gst-invoicing-app"
src_dir = os.path.join(base_dir, "src")

# 5. pdf_engine.py
pdf_engine_content = """# PDF Invoice Generator using ReportLab
import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

def generate_invoice_pdf(invoice: dict, items: list, company: dict) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=18, alignment=TA_CENTER, textColor=colors.HexColor('#1E3A8A'), fontName="Helvetica-Bold")
    sub_title = ParagraphStyle('SubTitle', fontSize=8, leading=10, alignment=TA_CENTER, textColor=colors.HexColor('#4B5563'))
    hdr_left = ParagraphStyle('HdrLeft', fontSize=9, leading=12, fontName="Helvetica-Bold", textColor=colors.HexColor('#1F2937'))
    txt_sm = ParagraphStyle('TxtSm', fontSize=8, leading=10, textColor=colors.HexColor('#374151'))
    txt_sm_bold = ParagraphStyle('TxtSmBold', fontSize=8, leading=10, fontName="Helvetica-Bold", textColor=colors.HexColor('#111827'))
    tbl_hdr = ParagraphStyle('TblHdr', fontSize=7.5, leading=9, fontName="Helvetica-Bold", alignment=TA_CENTER, textColor=colors.white)
    tbl_cell = ParagraphStyle('TblCell', fontSize=7.5, leading=9, textColor=colors.HexColor('#1F2937'))
    tbl_cell_center = ParagraphStyle('TblCellC', fontSize=7.5, leading=9, alignment=TA_CENTER, textColor=colors.HexColor('#1F2937'))
    tbl_cell_right = ParagraphStyle('TblCellR', fontSize=7.5, leading=9, alignment=TA_RIGHT, textColor=colors.HexColor('#1F2937'))
    tbl_cell_right_bold = ParagraphStyle('TblCellRB', fontSize=7.5, leading=9, fontName="Helvetica-Bold", alignment=TA_RIGHT, textColor=colors.HexColor('#111827'))

    story = []

    # Title Banner
    inv_type_text = "TAX INVOICE" if invoice.get('invoice_type') == 'B2B' else "INVOICE / BILL OF SUPPLY"
    story.append(Paragraph(f"<b>{inv_type_text}</b>", title_style))
    story.append(Paragraph("(Issued under Section 31 of Central Goods and Services Tax Act, 2017)", sub_title))
    story.append(Spacer(1, 4 * mm))

    # Company & Invoice Header Table
    is_interstate = bool(invoice.get('is_interstate'))
    comp_details = f\"\"\"
    <b><font size=10 color='#1E3A8A'>{company.get('name', 'My Business')}</font></b><br/>
    {company.get('address', '')}, {company.get('city', '')} - {company.get('pincode', '')}<br/>
    <b>GSTIN:</b> {company.get('gstin', '')} | <b>State:</b> {company.get('state', '')} ({company.get('state_code', '')})<br/>
    <b>Phone:</b> {company.get('phone', '')} | <b>Email:</b> {company.get('email', '')}
    \"\"\"

    inv_details = f\"\"\"
    <b>Invoice No:</b> <font color='#1E3A8A'>{invoice.get('invoice_number', '')}</font><br/>
    <b>Invoice Date:</b> {invoice.get('invoice_date', '')}<br/>
    <b>Due Date:</b> {invoice.get('due_date', 'Immediate')}<br/>
    <b>Place of Supply:</b> {invoice.get('place_of_supply', '')}<br/>
    <b>Tax Payable on RCM:</b> No
    \"\"\"

    header_table = Table(
        [[Paragraph(comp_details, txt_sm), Paragraph(inv_details, txt_sm)]],
        colWidths=[110 * mm, 80 * mm]
    )
    header_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#D1D5DB')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9FAFB')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 3 * mm))

    # Bill To / Ship To Section
    party_details = f\"\"\"
    <b>Billed To (Customer Details):</b><br/>
    <b><font size=9>{invoice.get('party_name', 'Cash Customer')}</font></b><br/>
    <b>Address:</b> {invoice.get('party_address', 'N/A')}<br/>
    <b>GSTIN / UIN:</b> {invoice.get('party_gstin') or 'Unregistered (B2C)'}<br/>
    <b>State:</b> {invoice.get('party_state', '')} (Code: {invoice.get('party_state_code', '')})
    \"\"\"

    dispatch_details = f\"\"\"
    <b>Shipped To (Delivery Address):</b><br/>
    <b>{invoice.get('party_name', '')}</b><br/>
    <b>Address:</b> {invoice.get('shipping_address') or invoice.get('party_address', 'Same as billing')}<br/>
    <b>Place of Supply:</b> {invoice.get('place_of_supply', '')}
    \"\"\"

    party_table = Table(
        [[Paragraph(party_details, txt_sm), Paragraph(dispatch_details, txt_sm)]],
        colWidths=[95 * mm, 95 * mm]
    )
    party_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#D1D5DB')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(party_table)
    story.append(Spacer(1, 3 * mm))

    # Line Items Table
    if is_interstate:
        # Columns: Sr, Item Description, HSN, Qty, Rate, Taxable, IGST (%), IGST (Amt), Total
        col_headers = [
            Paragraph("<b>#</b>", tbl_hdr),
            Paragraph("<b>Item Description</b>", tbl_hdr),
            Paragraph("<b>HSN/SAC</b>", tbl_hdr),
            Paragraph("<b>Qty</b>", tbl_hdr),
            Paragraph("<b>Rate (?)</b>", tbl_hdr),
            Paragraph("<b>Taxable (?)</b>", tbl_hdr),
            Paragraph("<b>IGST %</b>", tbl_hdr),
            Paragraph("<b>IGST Amt</b>", tbl_hdr),
            Paragraph("<b>Total (?)</b>", tbl_hdr),
        ]
        col_widths = [8*mm, 55*mm, 18*mm, 15*mm, 20*mm, 22*mm, 14*mm, 18*mm, 20*mm]
    else:
        # Columns: Sr, Item Description, HSN, Qty, Rate, Taxable, CGST Amt, SGST Amt, Total
        col_headers = [
            Paragraph("<b>#</b>", tbl_hdr),
            Paragraph("<b>Item Description</b>", tbl_hdr),
            Paragraph("<b>HSN/SAC</b>", tbl_hdr),
            Paragraph("<b>Qty</b>", tbl_hdr),
            Paragraph("<b>Rate (?)</b>", tbl_hdr),
            Paragraph("<b>Taxable (?)</b>", tbl_hdr),
            Paragraph("<b>CGST</b>", tbl_hdr),
            Paragraph("<b>SGST</b>", tbl_hdr),
            Paragraph("<b>Total (?)</b>", tbl_hdr),
        ]
        col_widths = [8*mm, 52*mm, 18*mm, 14*mm, 18*mm, 22*mm, 18*mm, 18*mm, 22*mm]

    table_data = [col_headers]

    for idx, item in enumerate(items, 1):
        if is_interstate:
            row = [
                Paragraph(str(idx), tbl_cell_center),
                Paragraph(f"<b>{item.get('item_name')}</b>", tbl_cell),
                Paragraph(str(item.get('hsn_code', '')), tbl_cell_center),
                Paragraph(f"{item.get('quantity')} {item.get('uom', '')}", tbl_cell_center),
                Paragraph(f"{item.get('rate', 0):,.2f}", tbl_cell_right),
                Paragraph(f"{item.get('taxable_value', 0):,.2f}", tbl_cell_right),
                Paragraph(f"{item.get('gst_rate', 0):.1f}%", tbl_cell_center),
                Paragraph(f"{item.get('igst_amount', 0):,.2f}", tbl_cell_right),
                Paragraph(f"{item.get('total', 0):,.2f}", tbl_cell_right_bold),
            ]
        else:
            cgst_txt = f"{item.get('cgst_amount', 0):,.2f}<br/><font size=6 color='#6B7280'>({item.get('cgst_rate', 0):.1f}%)</font>"
            sgst_txt = f"{item.get('sgst_amount', 0):,.2f}<br/><font size=6 color='#6B7280'>({item.get('sgst_rate', 0):.1f}%)</font>"
            row = [
                Paragraph(str(idx), tbl_cell_center),
                Paragraph(f"<b>{item.get('item_name')}</b>", tbl_cell),
                Paragraph(str(item.get('hsn_code', '')), tbl_cell_center),
                Paragraph(f"{item.get('quantity')} {item.get('uom', '')}", tbl_cell_center),
                Paragraph(f"{item.get('rate', 0):,.2f}", tbl_cell_right),
                Paragraph(f"{item.get('taxable_value', 0):,.2f}", tbl_cell_right),
                Paragraph(cgst_txt, tbl_cell_right),
                Paragraph(sgst_txt, tbl_cell_right),
                Paragraph(f"{item.get('total', 0):,.2f}", tbl_cell_right_bold),
            ]
        table_data.append(row)

    items_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#D1D5DB')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 2 * mm))

    # Summary & Bank Details Section
    bank_info = f\"\"\"
    <b>Bank Account Details:</b><br/>
    <b>Bank:</b> {company.get('bank_name', 'N/A')}<br/>
    <b>Account No:</b> {company.get('bank_acc', 'N/A')}<br/>
    <b>IFSC Code:</b> {company.get('bank_ifsc', 'N/A')}<br/>
    <b>Branch:</b> {company.get('bank_branch', '')}<br/>
    <b>UPI ID:</b> {company.get('upi_id', '')}
    \"\"\"

    taxable_val = float(invoice.get('taxable_amount', 0))
    cgst_val = float(invoice.get('cgst_amount', 0))
    sgst_val = float(invoice.get('sgst_amount', 0))
    igst_val = float(invoice.get('igst_amount', 0))
    round_off_val = float(invoice.get('round_off', 0))
    grand_total = float(invoice.get('total_amount', 0))

    calc_rows = [
        [Paragraph("Taxable Amount:", txt_sm), Paragraph(f"? {taxable_val:,.2f}", tbl_cell_right)],
    ]
    if is_interstate:
        calc_rows.append([Paragraph("Integrated GST (IGST):", txt_sm), Paragraph(f"? {igst_val:,.2f}", tbl_cell_right)])
    else:
        calc_rows.append([Paragraph("Central GST (CGST):", txt_sm), Paragraph(f"? {cgst_val:,.2f}", tbl_cell_right)])
        calc_rows.append([Paragraph("State GST (SGST):", txt_sm), Paragraph(f"? {sgst_val:,.2f}", tbl_cell_right)])

    if round_off_val != 0:
        calc_rows.append([Paragraph("Round Off:", txt_sm), Paragraph(f"? {round_off_val:+,.2f}", tbl_cell_right)])

    calc_rows.append([
        Paragraph("<b>Total Invoice Value:</b>", txt_sm_bold),
        Paragraph(f"<b><font size=10 color='#1E3A8A'>? {grand_total:,.2f}</font></b>", tbl_cell_right_bold)
    ])

    summary_calc_table = Table(calc_rows, colWidths=[45*mm, 45*mm])
    summary_calc_table.setStyle(TableStyle([
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#F3F4F6')),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))

    bottom_table = Table(
        [[Paragraph(bank_info, txt_sm), summary_calc_table]],
        colWidths=[100 * mm, 90 * mm]
    )
    bottom_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#D1D5DB')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9FAFB')),
    ]))
    story.append(bottom_table)
    story.append(Spacer(1, 2 * mm))

    # Amount in Words & Terms
    words_text = f"<b>Total Amount in Words:</b> <i>{invoice.get('amount_in_words', '')}</i>"
    story.append(Paragraph(words_text, txt_sm))
    story.append(Spacer(1, 3 * mm))

    terms_text = f\"\"\"
    <b>Terms & Conditions:</b><br/>
    {company.get('invoice_terms', '1. Payment due within invoice credit period. 2. Subject to local jurisdiction.').replace(chr(10), '<br/>')}
    \"\"\"

    sign_text = f\"\"\"
    For <b>{company.get('name', 'Company')}</b><br/><br/><br/>
    <b>Authorized Signatory</b>
    \"\"\"

    terms_sign_table = Table(
        [[Paragraph(terms_text, txt_sm), Paragraph(sign_text, ParagraphStyle('Sign', alignment=TA_RIGHT, fontSize=8, leading=11))]],
        colWidths=[120 * mm, 70 * mm]
    )
    terms_sign_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(terms_sign_table)

    doc.build(story)
    buffer.seek(0)
    return buffer
"""

# 6. excel_engine.py
excel_engine_content = """# GSTR-1 and GSTR-3B Excel Reports Generator
import io
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from typing import List, Dict, Any

def generate_gstr1_excel(sales_invoices: List[Dict[str, Any]], items_list: List[Dict[str, Any]]) -> io.BytesIO:
    wb = openpyxl.Workbook()
    
    # Styles
    hdr_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    hdr_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    bold_font = Font(name="Calibri", size=10, bold=True)
    regular_font = Font(name="Calibri", size=10)
    border_thin = Border(left=Side(style='thin', color='D1D5DB'),
                         right=Side(style='thin', color='D1D5DB'),
                         top=Side(style='thin', color='D1D5DB'),
                         bottom=Side(style='thin', color='D1D5DB'))

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
            18.0, # Standard default or weighted
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
    hsn_headers = ["HSN Code", "Description", "UQC", "Total Quantity", "Total Value", "Taxable Value", "Integrated Tax (?)", "Central Tax (?)", "State Tax (?)", "Cess (?)"]
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

    # Auto-adjust column widths
    for sheet in wb.worksheets:
        for col in sheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            sheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

def generate_gstr3b_excel(tax_summary: Dict[str, Any]) -> io.BytesIO:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "GSTR-3B Summary"

    hdr_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    hdr_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    section_fill = PatternFill(start_color="E0E7FF", end_color="E0E7FF", fill_type="solid")
    bold_font = Font(name="Calibri", size=10, bold=True)

    ws.append(["GSTR-3B Monthly Return Summary"])
    ws.merge_cells("A1:E1")
    ws.cell(row=1, column=1).font = Font(size=14, bold=True, color="1E3A8A")

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
        outward.get("total", 0.0), # Approximate or exact taxable
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

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
"""

with open(os.path.join(src_dir, "pdf_engine.py"), "w", encoding="utf-8") as f:
    f.write(pdf_engine_content)

with open(os.path.join(src_dir, "excel_engine.py"), "w", encoding="utf-8") as f:
    f.write(excel_engine_content)

print("pdf_engine.py and excel_engine.py created successfully!")
