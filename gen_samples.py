import os
import shutil

base_dir = r"C:\Users\One Click Solution\.gemini\antigravity\scratch\gst-invoicing-app"
uploads_dir = os.path.join(base_dir, "uploads")

# Let's generate a sample visual PDF in uploads/ for Delta Cloud & Metro Office
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_dummy_pdf(filename, title, vendor, gstin, amount, itc):
    filepath = os.path.join(uploads_dir, filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 720, title)
    c.setFont("Helvetica", 11)
    c.drawString(50, 690, f"Vendor / Supplier: {vendor}")
    c.drawString(50, 670, f"GSTIN: {gstin}")
    c.drawString(50, 650, f"Date: 05-Sep-2026 | Bill No: {filename.replace('.pdf', '')}")
    c.drawString(50, 630, f"Total Amount: INR {amount}")
    c.drawString(50, 610, f"Eligible Input Tax Credit (ITC): INR {itc}")
    c.line(50, 590, 550, 590)
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, 570, "Original Supplier Tax Invoice Copy (Attached for GST Audit & ITC Verification)")
    c.save()

create_dummy_pdf("sample_bill_deltacloud.pdf", "TAX INVOICE - DELTA CLOUD HARDWARE", "Delta Cloud Hardware Suppliers", "24AAACD4433E1Z9", "60,180.00", "9,180.00 (IGST)")
create_dummy_pdf("sample_bill_metro.pdf", "TAX INVOICE - METRO OFFICE & STATIONARY", "Metro Office & Stationary Hub", "27AABCM6677K1Z8", "14,336.00", "1,536.00 (CGST+SGST)")

print("Sample uploaded bill PDFs created successfully!")
