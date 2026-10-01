import os

base_dir = r"C:\Users\One Click Solution\.gemini\antigravity\scratch\gst-invoicing-app"
main_file = os.path.join(base_dir, "main.py")

with open(main_file, "r", encoding="utf-8") as f:
    content = f.read()

# Update CreateInvoiceSchema to include sales_person and party_email
if "sales_person: Optional[str] = 'SUFIYAN SHAIKH'" not in content:
    content = content.replace(
        "due_date: Optional[str] = None",
        "due_date: Optional[str] = None\n    sales_person: Optional[str] = 'SUFIYAN SHAIKH'\n    party_email: Optional[str] = ''"
    )

# Update INSERT INTO sales_invoices
old_insert = """    INSERT INTO sales_invoices (
        invoice_number, invoice_type, invoice_date, due_date, party_id, party_name,
        party_gstin, party_state, party_state_code, place_of_supply, is_interstate,
        taxable_amount, cgst_amount, sgst_amount, igst_amount, cess_amount,
        round_off, total_amount, amount_in_words, payment_status, amount_paid,
        balance_amount, payment_mode, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

new_insert = """    INSERT INTO sales_invoices (
        invoice_number, invoice_type, invoice_date, due_date, sales_person, party_id, party_name,
        party_gstin, party_email, party_state, party_state_code, place_of_supply, is_interstate,
        taxable_amount, cgst_amount, sgst_amount, igst_amount, cess_amount,
        round_off, total_amount, amount_in_words, payment_status, amount_paid,
        balance_amount, payment_mode, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

old_values = """        inv_num, payload.invoice_type, payload.invoice_date, payload.due_date, payload.party_id,
        payload.party_name, payload.party_gstin, payload.party_state, buyer_state_code, pos,
        1 if is_interstate else 0, calculated["taxable_amount"], calculated["cgst_amount"],
        calculated["sgst_amount"], calculated["igst_amount"], 0.0, calculated["round_off"],
        calculated["total_amount"], amount_words, payment_status, amt_paid, balance_amt,
        payload.payment_mode, payload.notes"""

new_values = """        inv_num, payload.invoice_type, payload.invoice_date, payload.due_date, payload.sales_person or 'SUFIYAN SHAIKH', payload.party_id,
        payload.party_name, payload.party_gstin, payload.party_email, payload.party_state, buyer_state_code, pos,
        1 if is_interstate else 0, calculated["taxable_amount"], calculated["cgst_amount"],
        calculated["sgst_amount"], calculated["igst_amount"], 0.0, calculated["round_off"],
        calculated["total_amount"], amount_words, payment_status, amt_paid, balance_amt,
        payload.payment_mode, payload.notes"""

content = content.replace(old_insert, new_insert)
content = content.replace(old_values, new_values)

with open(main_file, "w", encoding="utf-8") as f:
    f.write(content)

print("main.py updated successfully!")
