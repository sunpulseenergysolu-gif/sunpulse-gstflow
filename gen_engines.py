import os

base_dir = r"C:\Users\One Click Solution\.gemini\antigravity\scratch\gst-invoicing-app"
src_dir = os.path.join(base_dir, "src")

# 2. number_to_words.py
num_words_content = """# Indian Rupee Number to Words Converter

ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
        "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
        "Seventeen", "Eighteen", "Nineteen"]

TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

def _two_digits(num: int) -> str:
    if num == 0:
        return ""
    elif num < 20:
        return ONES[num]
    else:
        tens = TENS[num // 10]
        ones = ONES[num % 10]
        return f"{tens} {ones}".strip()

def _three_digits(num: int) -> str:
    hundred = num // 100
    remainder = num % 100
    res = []
    if hundred > 0:
        res.append(f"{ONES[hundred]} Hundred")
    if remainder > 0:
        res.append(_two_digits(remainder))
    return " ".join(res).strip()

def number_to_words_inr(amount: float) -> str:
    \"\"\"Converts a numerical amount into Indian Rupee Words (e.g. INR 1,25,450.50 -> One Lakh Twenty Five Thousand Four Hundred Fifty Rupees and Fifty Paise Only)\"\"\"
    try:
        amount = round(float(amount), 2)
    except (ValueError, TypeError):
        return "Zero Rupees Only"
        
    if amount == 0:
        return "Zero Rupees Only"

    rupees = int(amount)
    paise = int(round((amount - rupees) * 100))

    if rupees == 0 and paise > 0:
        return f"{_two_digits(paise)} Paise Only"

    parts = []
    
    # Crores (10,000,000)
    crores = rupees // 10000000
    rupees %= 10000000
    if crores > 0:
        parts.append(f"{_three_digits(crores)} Crore")

    # Lakhs (100,000)
    lakhs = rupees // 100000
    rupees %= 100000
    if lakhs > 0:
        parts.append(f"{_two_digits(lakhs)} Lakh")

    # Thousands (1,000)
    thousands = rupees // 1000
    rupees %= 1000
    if thousands > 0:
        parts.append(f"{_two_digits(thousands)} Thousand")

    # Hundreds and below
    if rupees > 0:
        parts.append(_three_digits(rupees))

    rupees_str = " ".join(parts).strip()
    result = f"{rupees_str} Rupees"

    if paise > 0:
        result += f" and {_two_digits(paise)} Paise"

    result += " Only"
    return result
"""

# 3. gst_engine.py
gst_engine_content = """# GST Engine - Calculation, Invoicing & Input Tax Credit (ITC) Logic
from typing import Dict, List, Any
import math

def calculate_line_item(rate: float, qty: float, discount_pct: float, gst_rate: float, is_interstate: bool):
    gross = float(rate) * float(qty)
    discount_val = (gross * float(discount_pct)) / 100.0
    taxable = max(0.0, gross - discount_val)
    
    gst_rate = float(gst_rate)
    total_tax = (taxable * gst_rate) / 100.0

    if is_interstate:
        cgst_rate = 0.0
        cgst_amt = 0.0
        sgst_rate = 0.0
        sgst_amt = 0.0
        igst_rate = gst_rate
        igst_amt = round(total_tax, 2)
    else:
        cgst_rate = gst_rate / 2.0
        cgst_amt = round(total_tax / 2.0, 2)
        sgst_rate = gst_rate / 2.0
        sgst_amt = round(total_tax / 2.0, 2)
        igst_rate = 0.0
        igst_amt = 0.0

    line_total = round(taxable + cgst_amt + sgst_amt + igst_amt, 2)

    return {
        "gross": round(gross, 2),
        "discount_amount": round(discount_val, 2),
        "taxable_value": round(taxable, 2),
        "gst_rate": gst_rate,
        "cgst_rate": cgst_rate,
        "cgst_amount": cgst_amt,
        "sgst_rate": sgst_rate,
        "sgst_amount": sgst_amt,
        "igst_rate": igst_rate,
        "igst_amount": igst_amt,
        "total": line_total
    }

def calculate_invoice_totals(items: List[Dict[str, Any]], is_interstate: bool, overall_discount: float = 0.0):
    total_taxable = 0.0
    total_cgst = 0.0
    total_sgst = 0.0
    total_igst = 0.0
    processed_items = []

    for it in items:
        rate = float(it.get("rate", 0))
        qty = float(it.get("quantity", 1))
        disc = float(it.get("discount_percent", 0))
        gst = float(it.get("gst_rate", 18))
        
        calc = calculate_line_item(rate, qty, disc, gst, is_interstate)
        merged = {**it, **calc}
        processed_items.append(merged)
        
        total_taxable += calc["taxable_value"]
        total_cgst += calc["cgst_amount"]
        total_sgst += calc["sgst_amount"]
        total_igst += calc["igst_amount"]

    # Overall invoice discount if any
    if overall_discount > 0:
        total_taxable = max(0.0, total_taxable - overall_discount)
        if is_interstate:
            # Recompute total igst proportionally or simple
            pass

    raw_total = total_taxable + total_cgst + total_sgst + total_igst
    final_total = round(raw_total)
    round_off = round(final_total - raw_total, 2)

    return {
        "items": processed_items,
        "taxable_amount": round(total_taxable, 2),
        "cgst_amount": round(total_cgst, 2),
        "sgst_amount": round(total_sgst, 2),
        "igst_amount": round(total_igst, 2),
        "total_tax": round(total_cgst + total_sgst + total_igst, 2),
        "round_off": round_off,
        "total_amount": float(final_total)
    }

def calculate_net_gst_liability(sales_invoices: List[Dict[str, Any]], purchase_bills: List[Dict[str, Any]]):
    \"\"\"Calculates Output GST liability vs Input Tax Credit (ITC) with detailed pool breakdown\"\"\"
    
    # 1. Output Tax Liability (From Sales)
    outward_cgst = sum(float(inv.get("cgst_amount", 0)) for inv in sales_invoices)
    outward_sgst = sum(float(inv.get("sgst_amount", 0)) for inv in sales_invoices)
    outward_igst = sum(float(inv.get("igst_amount", 0)) for inv in sales_invoices)
    total_output_tax = outward_cgst + outward_sgst + outward_igst

    # 2. Input Tax Credit - ITC (From Eligible Purchases)
    eligible_bills = [b for b in purchase_bills if b.get("itc_eligibility", "ELIGIBLE") == "ELIGIBLE"]
    ineligible_bills = [b for b in purchase_bills if b.get("itc_eligibility") == "INELIGIBLE_17_5"]
    
    itc_cgst = sum(float(b.get("cgst_amount", 0)) for b in eligible_bills)
    itc_sgst = sum(float(b.get("sgst_amount", 0)) for b in eligible_bills)
    itc_igst = sum(float(b.get("igst_amount", 0)) for b in eligible_bills)
    total_itc_available = itc_cgst + itc_sgst + itc_igst
    
    blocked_itc_total = sum(float(b.get("cgst_amount", 0)) + float(b.get("sgst_amount", 0)) + float(b.get("igst_amount", 0)) for b in ineligible_bills)

    # 3. GST Set-Off Rules Simulation
    # Rule: IGST credit used first for IGST, then CGST/SGST.
    # CGST credit used for CGST, then IGST (Never SGST).
    # SGST credit used for SGST, then IGST (Never CGST).
    
    rem_igst_liab = outward_igst
    rem_cgst_liab = outward_cgst
    rem_sgst_liab = outward_sgst

    rem_igst_itc = itc_igst
    rem_cgst_itc = itc_cgst
    rem_sgst_itc = itc_sgst

    # Offset IGST liability with IGST ITC
    used_igst_for_igst = min(rem_igst_liab, rem_igst_itc)
    rem_igst_liab -= used_igst_for_igst
    rem_igst_itc -= used_igst_for_igst

    # Offset CGST liability with IGST ITC if remaining
    used_igst_for_cgst = min(rem_cgst_liab, rem_igst_itc)
    rem_cgst_liab -= used_igst_for_cgst
    rem_igst_itc -= used_igst_for_cgst

    # Offset SGST liability with IGST ITC if remaining
    used_igst_for_sgst = min(rem_sgst_liab, rem_igst_itc)
    rem_sgst_liab -= used_igst_for_sgst
    rem_igst_itc -= used_igst_for_sgst

    # Offset CGST liability with CGST ITC
    used_cgst_for_cgst = min(rem_cgst_liab, rem_cgst_itc)
    rem_cgst_liab -= used_cgst_for_cgst
    rem_cgst_itc -= used_cgst_for_cgst

    # Offset IGST liability with CGST ITC if remaining
    used_cgst_for_igst = min(rem_igst_liab, rem_cgst_itc)
    rem_igst_liab -= used_cgst_for_igst
    rem_cgst_itc -= used_cgst_for_igst

    # Offset SGST liability with SGST ITC
    used_sgst_for_sgst = min(rem_sgst_liab, rem_sgst_itc)
    rem_sgst_liab -= used_sgst_for_sgst
    rem_sgst_itc -= used_sgst_for_sgst

    # Offset IGST liability with SGST ITC if remaining
    used_sgst_for_igst = min(rem_igst_liab, rem_sgst_itc)
    rem_igst_liab -= used_sgst_for_igst
    rem_sgst_itc -= used_sgst_for_igst

    net_tax_payable = rem_igst_liab + rem_cgst_liab + rem_sgst_liab
    closing_itc_balance = rem_igst_itc + rem_cgst_itc + rem_sgst_itc

    return {
        "output_tax": {
            "cgst": round(outward_cgst, 2),
            "sgst": round(outward_sgst, 2),
            "igst": round(outward_igst, 2),
            "total": round(total_output_tax, 2)
        },
        "input_tax_credit": {
            "cgst": round(itc_cgst, 2),
            "sgst": round(itc_sgst, 2),
            "igst": round(itc_igst, 2),
            "total": round(total_itc_available, 2),
            "blocked_itc": round(blocked_itc_total, 2)
        },
        "net_payable": {
            "cgst": round(rem_cgst_liab, 2),
            "sgst": round(rem_sgst_liab, 2),
            "igst": round(rem_igst_liab, 2),
            "total": round(net_tax_payable, 2)
        },
        "closing_credit_balance": {
            "cgst": round(rem_cgst_itc, 2),
            "sgst": round(rem_sgst_itc, 2),
            "igst": round(rem_igst_itc, 2),
            "total": round(closing_itc_balance, 2)
        }
    }
"""

with open(os.path.join(src_dir, "number_to_words.py"), "w", encoding="utf-8") as f:
    f.write(num_words_content)

with open(os.path.join(src_dir, "gst_engine.py"), "w", encoding="utf-8") as f:
    f.write(gst_engine_content)

print("number_to_words.py and gst_engine.py written successfully!")
