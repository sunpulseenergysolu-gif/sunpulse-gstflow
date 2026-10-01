import os

pdf_engine_file = r"C:\Users\One Click Solution\.gemini\antigravity\scratch\gst-invoicing-app\src\pdf_engine.py"

pdf_code = """# ReportLab PDF Invoice Engine matching SunPulse Energy Solutions exact layout
import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

def generate_invoice_pdf(invoice: dict, items: list, company: dict) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm
    )

    styles = getSampleStyleSheet()

    # Dark Blue brand color matching image #003366 / #002b66
    NAVY_BLUE = colors.HexColor('#002B66')
    GRAY_TEXT = colors.HexColor('#222222')
    DARK_TEXT = colors.HexColor('#111111')
    BORDER_COLOR = colors.HexColor('#333333')

    # Typography styles
    comp_title = ParagraphStyle('CompTitle', fontName='Helvetica-Bold', fontSize=10.5, leading=13, textColor=NAVY_BLUE, alignment=TA_RIGHT)
    comp_body = ParagraphStyle('CompBody', fontName='Helvetica', fontSize=8, leading=10.5, textColor=DARK_TEXT, alignment=TA_RIGHT)
    
    party_to = ParagraphStyle('PartyTo', fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=DARK_TEXT, alignment=TA_RIGHT)
    party_name_style = ParagraphStyle('PartyName', fontName='Helvetica-Bold', fontSize=9, leading=11.5, textColor=DARK_TEXT, alignment=TA_RIGHT)
    party_body = ParagraphStyle('PartyBody', fontName='Helvetica', fontSize=8, leading=10.5, textColor=DARK_TEXT, alignment=TA_RIGHT)
    party_gst = ParagraphStyle('PartyGst', fontName='Helvetica-Bold', fontSize=8, leading=10.5, textColor=DARK_TEXT, alignment=TA_RIGHT)

    inv_title = ParagraphStyle('InvTitle', fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=NAVY_BLUE)
    inv_meta_lbl = ParagraphStyle('InvMetaLbl', fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=NAVY_BLUE)
    inv_meta_val = ParagraphStyle('InvMetaVal', fontName='Helvetica', fontSize=8.5, leading=11, textColor=DARK_TEXT)

    tbl_hdr = ParagraphStyle('TblHdr', fontName='Helvetica-Bold', fontSize=7.5, leading=9, alignment=TA_CENTER, textColor=DARK_TEXT)
    tbl_hdr_left = ParagraphStyle('TblHdrL', fontName='Helvetica-Bold', fontSize=7.5, leading=9, alignment=TA_LEFT, textColor=DARK_TEXT)
    tbl_hdr_right = ParagraphStyle('TblHdrR', fontName='Helvetica-Bold', fontSize=7.5, leading=9, alignment=TA_RIGHT, textColor=DARK_TEXT)

    item_name = ParagraphStyle('ItemName', fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=DARK_TEXT)
    item_hsn = ParagraphStyle('ItemHsn', fontName='Helvetica', fontSize=7, leading=9, textColor=DARK_TEXT)
    item_cell = ParagraphStyle('ItemCell', fontName='Helvetica', fontSize=7.5, leading=9.5, alignment=TA_CENTER, textColor=DARK_TEXT)
    item_cell_right = ParagraphStyle('ItemCellR', fontName='Helvetica', fontSize=7.5, leading=9.5, alignment=TA_RIGHT, textColor=DARK_TEXT)

    tot_lbl = ParagraphStyle('TotLbl', fontName='Helvetica', fontSize=8, leading=10, textColor=DARK_TEXT)
    tot_val = ParagraphStyle('TotVal', fontName='Helvetica', fontSize=8, leading=10, alignment=TA_RIGHT, textColor=DARK_TEXT)
    grand_lbl = ParagraphStyle('GrandLbl', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=colors.white)
    grand_val = ParagraphStyle('GrandVal', fontName='Helvetica-Bold', fontSize=9, leading=11, alignment=TA_RIGHT, textColor=colors.white)

    footer_pg = ParagraphStyle('FooterPg', fontName='Helvetica', fontSize=7.5, leading=9, alignment=TA_CENTER, textColor=colors.HexColor('#666666'))

    story = []

    # 1. Top Section: Logo (Left) and Company + Customer Details (Right)
    logo_path = os.path.join(STATIC_DIR, "sunpulse_logo.jpg")
    if os.path.exists(logo_path):
        logo_img = Image(logo_path, width=58 * mm, height=36 * mm)
    else:
        logo_img = Paragraph(f"<b><font size=14 color='#002B66'>{company.get('name', 'SUNPULSE')}</font></b>", ParagraphStyle('LogoFallback'))

    # Company Details text
    comp_text = f\"\"\"
    <b>{company.get('name', 'SUNPULSE ENERGY SOLUTIONS')}</b><br/>
    {company.get('address', 'GF 56/4, CHHIPA NI CHALI/JUNI CHALI<br/>RAKHIYAL, Ahmedabad').replace(chr(10), '<br/>')}<br/>
    {company.get('city', 'AHMEDABAD')} {company.get('pincode', '380023')}<br/>
    {company.get('state', 'Gujarat')} GJ<br/>
    {company.get('country', 'India')}<br/>
    GSTIN: {company.get('gstin', '24MVMPS3622M1ZT')}
    \"\"\"

    # Customer Details text
    customer_name = invoice.get('party_name', '')
    customer_addr = invoice.get('party_address', '511, City Center<br/>Science City Road, Ahmedabad,<br/>380060, Gujarat GJ(India)').replace(chr(10), '<br/>')
    customer_gst = invoice.get('party_gstin', '')
    customer_email = invoice.get('party_email', '')

    customer_text = f\"\"\"
    <b>To,</b><br/>
    <b>{customer_name}</b><br/>
    {customer_addr}<br/>
    <b>GSTNO:{customer_gst}</b><br/>
    {customer_email}
    \"\"\"

    right_col = [
        Paragraph(comp_text, comp_body),
        Spacer(1, 4 * mm),
        Paragraph(customer_text, party_body)
    ]

    header_table = Table(
        [[logo_img, right_col]],
        colWidths=[65 * mm, 117 * mm]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8 * mm))

    # 2. Invoice Title, Date & Sales Person
    inv_num_clean = invoice.get('invoice_number', 'INVOICE/01')
    story.append(Paragraph(f"<b>{inv_num_clean}</b>", inv_title))
    story.append(Spacer(1, 3 * mm))

    inv_date_val = invoice.get('invoice_date', '')
    # Format YYYY-MM-DD to DD/MM/YYYY if needed
    if '-' in inv_date_val:
        parts = inv_date_val.split('-')
        if len(parts) == 3 and len(parts[0]) == 4:
            inv_date_val = f"{parts[2]}/{parts[1]}/{parts[0]}"

    sales_person_val = invoice.get('sales_person', 'SUFIYAN SHAIKH')

    meta_table = Table(
        [
            [Paragraph("<b>Invoice Date:</b>", inv_meta_lbl), Paragraph("<b>Sales person:</b>", inv_meta_lbl)],
            [Paragraph(inv_date_val, inv_meta_val), Paragraph(sales_person_val, inv_meta_val)]
        ],
        colWidths=[65 * mm, 117 * mm]
    )
    meta_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 4 * mm))

    # 3. Items Table
    # Header: DESCRIPTION | QUANTITY | UNIT PRICE | TAXES | AMOUNT
    col_widths = [82 * mm, 24 * mm, 24 * mm, 22 * mm, 30 * mm]
    table_data = [
        [
            Paragraph("<b>DESCRIPTION</b>", tbl_hdr_left),
            Paragraph("<b>QUANTITY</b>", tbl_hdr),
            Paragraph("<b>UNIT PRICE</b>", tbl_hdr),
            Paragraph("<b>TAXES</b>", tbl_hdr),
            Paragraph("<b>AMOUNT</b>", tbl_hdr)
        ]
    ]

    total_untaxed = 0.0
    total_sgst = 0.0
    total_cgst = 0.0
    total_igst = 0.0
    is_interstate = bool(invoice.get('is_interstate', 0))

    for item in items:
        hsn_str = f"HSN/SAC Code:{item.get('hsn_code', '')}" if item.get('hsn_code') else ""
        desc_para = Paragraph(f"<b>{item.get('item_name')}</b><br/><font size=6.5 color='#333333'>{hsn_str}</font>", item_name)
        
        qty_str = f"{item.get('quantity', 1):.2f} {item.get('uom', '')}"
        rate_val = float(item.get('rate', 0))
        gst_pct = float(item.get('gst_rate', 0))
        taxable_val = float(item.get('taxable_value', rate_val * float(item.get('quantity', 1))))
        
        tax_str = f"GST{gst_pct:.0f}%"

        table_data.append([
            desc_para,
            Paragraph(qty_str, item_cell),
            Paragraph(f"{rate_val:,.2f}", item_cell_right),
            Paragraph(tax_str, item_cell),
            Paragraph(f"₹ {taxable_val:,.2f}", item_cell_right)
        ])

    items_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.75, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 2 * mm))

    # 4. Totals Summary Box (Right Aligned)
    untaxed_amount = float(invoice.get('taxable_amount', 0))
    sgst_amount = float(invoice.get('sgst_amount', 0))
    cgst_amount = float(invoice.get('cgst_amount', 0))
    igst_amount = float(invoice.get('igst_amount', 0))
    total_val = float(invoice.get('total_amount', 0))

    summary_rows = [
        [Paragraph("Untaxed Amount", tot_lbl), Paragraph(f"₹ {untaxed_amount:,.2f}", tot_val)]
    ]

    if is_interstate:
        summary_rows.append([Paragraph("IGST", tot_lbl), Paragraph(f"₹ {igst_amount:,.2f}", tot_val)])
    else:
        summary_rows.append([Paragraph("SGST", tot_lbl), Paragraph(f"₹ {sgst_amount:,.2f}", tot_val)])
        summary_rows.append([Paragraph("CGST", tot_lbl), Paragraph(f"₹ {cgst_amount:,.2f}", tot_val)])

    summary_rows.append([
        Paragraph("<b>Total</b>", grand_lbl),
        Paragraph(f"<b>₹ {total_val:,.2f}</b>", grand_val)
    ])

    summary_table = Table(summary_rows, colWidths=[52 * mm, 34 * mm])
    summary_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.75, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -2), 0.5, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -2), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -2), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('BACKGROUND', (0, -1), (-1, -1), NAVY_BLUE),
        ('TOPPADDING', (0, -1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 4),
    ]))

    # Align summary table to right by placing in outer table
    outer_totals_table = Table(
        [[Paragraph("", tot_lbl), summary_table]],
        colWidths=[96 * mm, 86 * mm]
    )
    outer_totals_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(outer_totals_table)

    # 5. Bottom Page & Horizontal Rule
    story.append(Spacer(1, 30 * mm))
    story.append(Paragraph("Page:1/1", footer_pg))
    story.append(Spacer(1, 2 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=1, spaceAfter=1))

    doc.build(story)
    buffer.seek(0)
    return buffer
"""

with open(pdf_engine_file, "w", encoding="utf-8") as f:
    f.write(pdf_code)

print("pdf_engine.py updated with exact SunPulse invoice design!")
