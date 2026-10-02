# ReportLab PDF Invoice Engine - Standard A4 Single-Page Compliant Layout
import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from src.number_to_words import number_to_words_inr

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

def format_inr(amount: float, show_symbol: bool = True) -> str:
    try:
        val = float(amount or 0)
    except (ValueError, TypeError):
        val = 0.0
    s = f"{abs(val):.2f}"
    parts = s.split('.')
    integer_part = parts[0]
    decimal_part = parts[1]
    if len(integer_part) > 3:
        last3 = integer_part[-3:]
        remaining = integer_part[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        formatted_int = ",".join(groups) + "," + last3
    else:
        formatted_int = integer_part
    sign = "-" if val < 0 else ""
    formatted = f"{sign}{formatted_int}.{decimal_part}"
    return f"Rs. {formatted}" if show_symbol else formatted

def generate_invoice_pdf(invoice: dict, items: list, company: dict) -> io.BytesIO:
    buffer = io.BytesIO()
    
    # A4 Dimensions: 210mm x 297mm. With 10mm margins, printable area is 190mm x 277mm.
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm
    )

    styles = getSampleStyleSheet()

    # Brand Colors matching SunPulse Energy Solutions exact layout
    NAVY_BLUE = colors.HexColor('#002B66')
    DARK_TEXT = colors.HexColor('#111111')
    MUTED_TEXT = colors.HexColor('#444444')
    BORDER_COLOR = colors.HexColor('#222222')
    LIGHT_BORDER = colors.HexColor('#999999')
    BG_LIGHT = colors.HexColor('#F8FAFC')

    # Typography styles
    comp_title = ParagraphStyle('CompTitle', fontName='Helvetica-Bold', fontSize=10, leading=12.5, textColor=NAVY_BLUE, alignment=TA_RIGHT)
    comp_body = ParagraphStyle('CompBody', fontName='Helvetica', fontSize=7.5, leading=10, textColor=DARK_TEXT, alignment=TA_RIGHT)
    
    party_body = ParagraphStyle('PartyBody', fontName='Helvetica', fontSize=7.5, leading=10, textColor=DARK_TEXT, alignment=TA_RIGHT)

    inv_title = ParagraphStyle('InvTitle', fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=NAVY_BLUE)
    inv_meta_lbl = ParagraphStyle('InvMetaLbl', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=NAVY_BLUE)
    inv_meta_val = ParagraphStyle('InvMetaVal', fontName='Helvetica', fontSize=8, leading=10, textColor=DARK_TEXT)

    tbl_hdr = ParagraphStyle('TblHdr', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, alignment=TA_CENTER, textColor=DARK_TEXT)
    tbl_hdr_left = ParagraphStyle('TblHdrL', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, alignment=TA_LEFT, textColor=DARK_TEXT)
    tbl_hdr_right = ParagraphStyle('TblHdrR', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, alignment=TA_RIGHT, textColor=DARK_TEXT)

    item_name = ParagraphStyle('ItemName', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=DARK_TEXT)
    item_hsn = ParagraphStyle('ItemHsn', fontName='Helvetica', fontSize=6.5, leading=8.5, textColor=MUTED_TEXT)
    item_cell = ParagraphStyle('ItemCell', fontName='Helvetica', fontSize=7.5, leading=9.5, alignment=TA_CENTER, textColor=DARK_TEXT)
    item_cell_right = ParagraphStyle('ItemCellR', fontName='Helvetica', fontSize=7.5, leading=9.5, alignment=TA_RIGHT, textColor=DARK_TEXT)

    tot_lbl = ParagraphStyle('TotLbl', fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=DARK_TEXT)
    tot_val = ParagraphStyle('TotVal', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, alignment=TA_RIGHT, textColor=DARK_TEXT)
    grand_lbl = ParagraphStyle('GrandLbl', fontName='Helvetica-Bold', fontSize=8.5, leading=10.5, textColor=colors.white)
    grand_val = ParagraphStyle('GrandVal', fontName='Helvetica-Bold', fontSize=8.5, leading=10.5, alignment=TA_RIGHT, textColor=colors.white)

    sec_title = ParagraphStyle('SecTitle', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=NAVY_BLUE)
    sec_content = ParagraphStyle('SecContent', fontName='Helvetica', fontSize=7, leading=9, textColor=DARK_TEXT)
    notes_bold = ParagraphStyle('NotesBold', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=DARK_TEXT)
    notes_content = ParagraphStyle('NotesContent', fontName='Helvetica', fontSize=7, leading=9, textColor=DARK_TEXT)

    sign_style = ParagraphStyle('SignStyle', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, alignment=TA_RIGHT, textColor=DARK_TEXT)
    footer_pg = ParagraphStyle('FooterPg', fontName='Helvetica', fontSize=7, leading=8.5, alignment=TA_CENTER, textColor=colors.HexColor('#666666'))

    story = []

    # -------------------------------------------------------------
    # 1. Top Section: Logo (Left) and Company + Customer Details (Right)
    # -------------------------------------------------------------
    logo_path = os.path.join(STATIC_DIR, "sunpulse_logo.jpg")
    if os.path.exists(logo_path):
        logo_img = Image(logo_path, width=54 * mm, height=32 * mm)
    else:
        logo_img = Paragraph(f"<b><font size=13 color='#002B66'>{company.get('name', 'SUNPULSE')}</font></b>", ParagraphStyle('LogoFallback'))

    # Company text
    comp_text = f"""
    <b>{company.get('name', 'SUNPULSE ENERGY SOLUTIONS')}</b><br/>
    {company.get('address', 'GF 56/4, CHHIPA NI CHALI/JUNI CHALI<br/>RAKHIYAL, Ahmedabad').replace(chr(10), '<br/>')}<br/>
    {company.get('city', 'AHMEDABAD')} {company.get('pincode', '380023')}<br/>
    {company.get('state', 'Gujarat')} GJ<br/>
    {company.get('country', 'India')}<br/>
    GSTIN: {company.get('gstin', '24MVMPS3622M1ZT')}
    """

    # Customer text
    customer_name = invoice.get('party_name', 'Customer')
    customer_addr = invoice.get('party_address', '').replace(chr(10), '<br/>')
    if not customer_addr:
        customer_addr = f"{invoice.get('party_state', 'Gujarat')} (India)"
    customer_gst = invoice.get('party_gstin', 'N/A')
    customer_email = invoice.get('party_email', '')

    customer_text = f"""
    <b>To,</b><br/>
    <b>{customer_name}</b><br/>
    {customer_addr}<br/>
    <b>GSTNO:{customer_gst}</b>
    {f'<br/>{customer_email}' if customer_email else ''}
    """

    right_col = [
        Paragraph(comp_text, comp_body),
        Spacer(1, 2.5 * mm),
        Paragraph(customer_text, party_body)
    ]

    header_table = Table(
        [[logo_img, right_col]],
        colWidths=[60 * mm, 130 * mm]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4 * mm))

    # -------------------------------------------------------------
    # 2. Invoice Title, Date & Sales Person
    # -------------------------------------------------------------
    inv_num_clean = invoice.get('invoice_number', 'INVOICE/01')
    inv_date_val = invoice.get('invoice_date', '')
    if '-' in inv_date_val:
        parts = inv_date_val.split('-')
        if len(parts) == 3 and len(parts[0]) == 4:
            inv_date_val = f"{parts[2]}/{parts[1]}/{parts[0]}"

    sales_person_val = invoice.get('sales_person', 'SUFIYAN SHAIKH')

    inv_meta_table = Table(
        [
            [
                Paragraph(f"<b>{inv_num_clean}</b>", inv_title),
                Table([
                    [Paragraph("<b>Invoice Date:</b>", inv_meta_lbl), Paragraph("<b>Sales person:</b>", inv_meta_lbl)],
                    [Paragraph(inv_date_val, inv_meta_val), Paragraph(sales_person_val.upper(), inv_meta_val)]
                ], colWidths=[65 * mm, 65 * mm])
            ]
        ],
        colWidths=[60 * mm, 130 * mm]
    )
    inv_meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(inv_meta_table)
    story.append(Spacer(1, 3 * mm))

    # -------------------------------------------------------------
    # 3. Items Table (Total Width: 190mm)
    # -------------------------------------------------------------
    # Col Widths: 76mm (Desc) + 26mm (Qty) + 28mm (Unit Price) + 24mm (Taxes) + 36mm (Amount) = 190mm
    col_widths = [76 * mm, 26 * mm, 28 * mm, 24 * mm, 36 * mm]
    table_data = [
        [
            Paragraph("<b>DESCRIPTION</b>", tbl_hdr_left),
            Paragraph("<b>QUANTITY</b>", tbl_hdr),
            Paragraph("<b>UNIT PRICE</b>", tbl_hdr),
            Paragraph("<b>TAXES</b>", tbl_hdr),
            Paragraph("<b>AMOUNT</b>", tbl_hdr)
        ]
    ]

    is_interstate = bool(invoice.get('is_interstate', 0))

    for item in items:
        hsn_str = f"HSN/SAC Code:{item.get('hsn_code', '')}" if item.get('hsn_code') else ""
        desc_cell = [
            Paragraph(f"<b>{item.get('item_name', '')}</b>", item_name)
        ]
        if hsn_str:
            desc_cell.append(Paragraph(hsn_str, item_hsn))
        
        qty_str = f"{float(item.get('quantity', 1)):.3f} {item.get('uom', 'Units')}"
        rate_val = float(item.get('rate', 0))
        gst_pct = float(item.get('gst_rate', 0))
        taxable_val = float(item.get('taxable_value', rate_val * float(item.get('quantity', 1))))
        
        tax_str = f"GST{gst_pct:g}%"

        table_data.append([
            desc_cell,
            Paragraph(qty_str, item_cell),
            Paragraph(format_inr(rate_val, show_symbol=False), item_cell_right),
            Paragraph(tax_str, item_cell),
            Paragraph(format_inr(taxable_val, show_symbol=False), item_cell_right)
        ])

    items_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.75, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 2.5 * mm))

    # -------------------------------------------------------------
    # 4. Bottom Section: Left Column (Words + Bank + Notes + Terms) & Right Column (Totals + Signatory)
    # Total Width: 190mm (Left: 108mm, Right: 82mm)
    # -------------------------------------------------------------
    untaxed_amount = float(invoice.get('taxable_amount', 0))
    sgst_amount = float(invoice.get('sgst_amount', 0))
    cgst_amount = float(invoice.get('cgst_amount', 0))
    igst_amount = float(invoice.get('igst_amount', 0))
    total_val = float(invoice.get('total_amount', 0))

    # Amount in words
    amt_words = invoice.get('amount_in_words') or number_to_words_inr(total_val)

    # Prepare Left Column Items
    left_flowables = []

    # Amount in words paragraph
    left_flowables.append(Paragraph(f"<b>Amount Chargeable (in words):</b><br/><i>{amt_words}</i>", sec_content))
    left_flowables.append(Spacer(1, 2 * mm))

    # Bank Details (if configured)
    bank_name = company.get('bank_name') or 'HDFC Bank Ltd'
    bank_acc = company.get('bank_acc') or '50200084729101'
    bank_ifsc = company.get('bank_ifsc') or 'HDFC0001024'
    bank_branch = company.get('bank_branch') or 'Ahmedabad Branch'
    upi_id = company.get('upi_id') or 'sunpulse@hdfcbank'

    bank_details_html = f"<b>Company Bank Details:</b><br/>Bank: <b>{bank_name}</b> | A/C No: <b>{bank_acc}</b><br/>IFSC Code: <b>{bank_ifsc}</b> | Branch: <b>{bank_branch}</b> | UPI: <b>{upi_id}</b>"
    
    bank_table = Table([[Paragraph(bank_details_html, sec_content)]], colWidths=[106 * mm])
    bank_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, LIGHT_BORDER),
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    left_flowables.append(bank_table)
    left_flowables.append(Spacer(1, 2 * mm))

    # User's Custom Notes / Remarks (Prominently rendered at the bottom)
    user_notes = (invoice.get('notes') or '').strip()
    if user_notes:
        notes_html = f"<b>Notes / Remarks:</b><br/>{user_notes.replace(chr(10), '<br/>')}"
        notes_table = Table([[Paragraph(notes_html, notes_content)]], colWidths=[106 * mm])
        notes_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.6, NAVY_BLUE),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F7FF')),
            ('TOPPADDING', (0, 0), (-1, -1), 3.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 4.5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4.5),
        ]))
        left_flowables.append(notes_table)
        left_flowables.append(Spacer(1, 2 * mm))

    # Company Terms and Conditions
    terms_text = (company.get('invoice_terms') or '').strip()
    if not terms_text:
        terms_text = f"1. Goods once sold will not be taken back.\n2. Warranty as per standard manufacturer policy.\n3. Subject to {company.get('city', 'Ahmedabad')} Jurisdiction."
    terms_html = f"<b>Terms & Conditions:</b><br/>{terms_text.replace(chr(10), '<br/>')}"
    left_flowables.append(Paragraph(terms_html, sec_content))

    # Prepare Right Column: Totals Summary + Signatory
    summary_rows = [
        [Paragraph("Untaxed Amount", tot_lbl), Paragraph(format_inr(untaxed_amount, show_symbol=True), tot_val)]
    ]

    if is_interstate:
        summary_rows.append([Paragraph("IGST", tot_lbl), Paragraph(format_inr(igst_amount, show_symbol=True), tot_val)])
    else:
        summary_rows.append([Paragraph("SGST", tot_lbl), Paragraph(format_inr(sgst_amount, show_symbol=True), tot_val)])
        summary_rows.append([Paragraph("CGST", tot_lbl), Paragraph(format_inr(cgst_amount, show_symbol=True), tot_val)])

    summary_rows.append([
        Paragraph("<b>Total</b>", grand_lbl),
        Paragraph(f"<b>{format_inr(total_val, show_symbol=True)}</b>", grand_val)
    ])

    summary_table = Table(summary_rows, colWidths=[48 * mm, 34 * mm])
    summary_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.75, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -2), 0.5, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -2), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -2), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, -1), (-1, -1), NAVY_BLUE),
        ('TOPPADDING', (0, -1), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 3.5),
    ]))

    comp_name_str = company.get('name', 'SUNPULSE ENERGY SOLUTIONS')
    signatory_html = f"<b>For {comp_name_str}</b><br/><br/><br/><br/><b>Authorized Signatory</b>"

    right_col_content = [
        summary_table,
        Spacer(1, 4 * mm),
        Paragraph(signatory_html, sign_style)
    ]

    bottom_container_table = Table(
        [[left_flowables, right_col_content]],
        colWidths=[108 * mm, 82 * mm]
    )
    bottom_container_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    story.append(bottom_container_table)

    # -------------------------------------------------------------
    # 5. Bottom Footer (Single-Page Indicator & Horizontal Rule)
    # -------------------------------------------------------------
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("Page:1/1", footer_pg))
    story.append(Spacer(1, 1 * mm))
    story.append(HRFlowable(width="100%", thickness=0.75, color=colors.black, spaceBefore=0, spaceAfter=0))

    doc.build(story)
    buffer.seek(0)
    return buffer

