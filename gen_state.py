import os
import sqlite3
import json

base_dir = r"C:\Users\One Click Solution\.gemini\antigravity\scratch\gst-invoicing-app"
src_dir = os.path.join(base_dir, "src")
uploads_dir = os.path.join(base_dir, "uploads")
static_dir = os.path.join(base_dir, "static")

os.makedirs(src_dir, exist_ok=True)
os.makedirs(uploads_dir, exist_ok=True)
os.makedirs(static_dir, exist_ok=True)

# 1. state_codes.py
state_codes_content = """# GST State Codes Master of India
GST_STATES = [
    {"code": "01", "name": "Jammu and Kashmir"},
    {"code": "02", "name": "Himachal Pradesh"},
    {"code": "03", "name": "Punjab"},
    {"code": "04", "name": "Chandigarh"},
    {"code": "05", "name": "Uttarakhand"},
    {"code": "06", "name": "Haryana"},
    {"code": "07", "name": "Delhi"},
    {"code": "08", "name": "Rajasthan"},
    {"code": "09", "name": "Uttar Pradesh"},
    {"code": "10", "name": "Bihar"},
    {"code": "11", "name": "Sikkim"},
    {"code": "12", "name": "Arunachal Pradesh"},
    {"code": "13", "name": "Nagaland"},
    {"code": "14", "name": "Manipur"},
    {"code": "15", "name": "Mizoram"},
    {"code": "16", "name": "Tripura"},
    {"code": "17", "name": "Meghalaya"},
    {"code": "18", "name": "Assam"},
    {"code": "19", "name": "West Bengal"},
    {"code": "20", "name": "Jharkhand"},
    {"code": "21", "name": "Odisha"},
    {"code": "22", "name": "Chhattisgarh"},
    {"code": "23", "name": "Madhya Pradesh"},
    {"code": "24", "name": "Gujarat"},
    {"code": "26", "name": "Dadra and Nagar Haveli and Daman and Diu"},
    {"code": "27", "name": "Maharashtra"},
    {"code": "28", "name": "Andhra Pradesh (Old)"},
    {"code": "29", "name": "Karnataka"},
    {"code": "30", "name": "Goa"},
    {"code": "31", "name": "Lakshadweep"},
    {"code": "32", "name": "Kerala"},
    {"code": "33", "name": "Tamil Nadu"},
    {"code": "34", "name": "Puducherry"},
    {"code": "35", "name": "Andaman and Nicobar Islands"},
    {"code": "36", "name": "Telangana"},
    {"code": "37", "name": "Andhra Pradesh (New)"},
    {"code": "38", "name": "Ladakh"},
    {"code": "97", "name": "Other Territory"},
    {"code": "99", "name": "Centre Jurisdiction"}
]

def get_state_name_by_code(code: str) -> str:
    code_str = str(code).strip().zfill(2)
    for s in GST_STATES:
        if s["code"] == code_str:
            return s["name"]
    return "Unknown State"

def get_state_code_from_gstin(gstin: str) -> str:
    if gstin and len(gstin.strip()) >= 2:
        return gstin.strip()[:2]
    return ""
"""

with open(os.path.join(src_dir, "state_codes.py"), "w", encoding="utf-8") as f:
    f.write(state_codes_content)

print("state_codes.py written successfully!")
