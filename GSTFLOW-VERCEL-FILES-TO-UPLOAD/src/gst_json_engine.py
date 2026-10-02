# GST Portal Direct Upload JSON Engine (GSTR-1 & GSTR-3B GSTN Schema Compliant)
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

def format_date_for_gstn(date_str: str) -> str:
    """Converts YYYY-MM-DD to DD-MM-YYYY required by GST Portal."""
    if not date_str:
        return ""
    try:
        parts = str(date_str).split("-")
        if len(parts) == 3:
            return f"{parts[2]}-{parts[1]}-{parts[0]}"
    except Exception:
        pass
    return str(date_str)

def get_return_period_fp(month: Optional[str], fy: Optional[str], invoices: List[Dict[str, Any]]) -> str:
    """Returns 6-digit period string MMYYYY (e.g., '092026') for GST Portal."""
    if month and str(month).isdigit():
        m_num = int(month)
        if fy and "-" in str(fy):
            parts = str(fy).replace("FY", "").strip().split("-")
            start_yr = int(parts[0])
            end_yr = 2000 + int(parts[1]) if len(parts[1]) == 2 else int(parts[1])
            yr = start_yr if m_num >= 4 else end_yr
            return f"{m_num:02d}{yr}"
    
    for inv in invoices:
        d = inv.get("invoice_date") or inv.get("bill_date")
        if d and len(str(d)) >= 7:
            parts = str(d).split("-")
            return f"{parts[1]}{parts[0]}"
    
    now = datetime.now()
    return f"{now.month:02d}{now.year}"

def generate_gstr1_json(
    company: Dict[str, Any],
    sales_invoices: List[Dict[str, Any]],
    items_list: List[Dict[str, Any]],
    period_month: Optional[str] = None,
    period_fy: Optional[str] = None
) -> str:
    """
    Generates official GSTN Offline Tool compliant GSTR-1 JSON
    for direct upload to https://services.gst.gov.in
    """
    gstin = company.get("gstin", "24MVMPS3622M1ZT")
    fp = get_return_period_fp(period_month, period_fy, sales_invoices)
    
    items_by_inv = {}
    for itm in items_list:
        inv_id = itm.get("invoice_id")
        if inv_id not in items_by_inv:
            items_by_inv[inv_id] = []
        items_by_inv[inv_id].append(itm)

    b2b_by_ctin = {}
    b2cs_list = []
    total_taxable_all = 0.0

    for inv in sales_invoices:
        inv_id = inv.get("id")
        inv_type = inv.get("invoice_type", "B2B")
        party_gstin = (inv.get("party_gstin") or "").strip().upper()
        pos = (inv.get("party_state_code") or inv.get("place_of_supply") or "24")[:2].zfill(2)
        inv_date = format_date_for_gstn(inv.get("invoice_date", ""))
        inv_num = str(inv.get("invoice_number", ""))
        inv_val = round(float(inv.get("total_amount", 0.0)), 2)
        total_taxable_all += float(inv.get("taxable_amount", 0.0))

        inv_items = items_by_inv.get(inv_id, [])
        itms_json = []
        if inv_items:
            for idx, itm in enumerate(inv_items, 1):
                rate = round(float(itm.get("gst_rate", 18.0)), 2)
                txval = round(float(itm.get("taxable_value", 0.0)), 2)
                camt = round(float(itm.get("cgst_amount", 0.0)), 2)
                samt = round(float(itm.get("sgst_amount", 0.0)), 2)
                iamt = round(float(itm.get("igst_amount", 0.0)), 2)
                
                itms_json.append({
                    "num": idx,
                    "itm_det": {
                        "rt": rate,
                        "txval": txval,
                        "iamt": iamt,
                        "camt": camt,
                        "samt": samt,
                        "csamt": 0.0
                    }
                })
        else:
            itms_json.append({
                "num": 1,
                "itm_det": {
                    "rt": 18.0,
                    "txval": round(float(inv.get("taxable_amount", 0.0)), 2),
                    "iamt": round(float(inv.get("igst_amount", 0.0)), 2),
                    "camt": round(float(inv.get("cgst_amount", 0.0)), 2),
                    "samt": round(float(inv.get("sgst_amount", 0.0)), 2),
                    "csamt": 0.0
                }
            })

        if inv_type == "B2B" and len(party_gstin) >= 15:
            if party_gstin not in b2b_by_ctin:
                b2b_by_ctin[party_gstin] = []
            
            b2b_by_ctin[party_gstin].append({
                "inum": inv_num,
                "idt": inv_date,
                "val": inv_val,
                "pos": pos,
                "rchrg": "N",
                "etin": "",
                "inv_typ": "R",
                "itms": itms_json
            })
        else:
            is_interstate = int(inv.get("is_interstate", 0))
            sply_ty = "INTER" if is_interstate else "INTRA"
            for itm in itms_json:
                det = itm["itm_det"]
                b2cs_list.append({
                    "sply_ty": sply_ty,
                    "rt": det["rt"],
                    "typ": "OE",
                    "pos": pos,
                    "txval": det["txval"],
                    "iamt": det["iamt"],
                    "camt": det["camt"],
                    "samt": det["samt"],
                    "csamt": 0.0
                })

    b2b_formatted = []
    for ctin, invs in b2b_by_ctin.items():
        b2b_formatted.append({
            "ctin": ctin,
            "cflag": "N",
            "inv": invs
        })

    # HSN Summary
    hsn_dict = {}
    for itm in items_list:
        hsn = str(itm.get("hsn_code") or "998719").strip()
        desc = str(itm.get("item_name") or "Goods / Services")
        uqc = str(itm.get("uom") or "PCS").upper()
        qty = float(itm.get("quantity", 1.0))
        txval = float(itm.get("taxable_value", 0.0))
        camt = float(itm.get("cgst_amount", 0.0))
        samt = float(itm.get("sgst_amount", 0.0))
        iamt = float(itm.get("igst_amount", 0.0))
        tot = float(itm.get("total", txval + camt + samt + iamt))

        if hsn not in hsn_dict:
            hsn_dict[hsn] = {
                "hsn_sc": hsn,
                "desc": desc,
                "uqc": uqc,
                "qty": 0.0,
                "val": 0.0,
                "txval": 0.0,
                "iamt": 0.0,
                "camt": 0.0,
                "samt": 0.0,
                "csamt": 0.0
            }
        hsn_dict[hsn]["qty"] = round(hsn_dict[hsn]["qty"] + qty, 2)
        hsn_dict[hsn]["val"] = round(hsn_dict[hsn]["val"] + tot, 2)
        hsn_dict[hsn]["txval"] = round(hsn_dict[hsn]["txval"] + txval, 2)
        hsn_dict[hsn]["iamt"] = round(hsn_dict[hsn]["iamt"] + iamt, 2)
        hsn_dict[hsn]["camt"] = round(hsn_dict[hsn]["camt"] + camt, 2)
        hsn_dict[hsn]["samt"] = round(hsn_dict[hsn]["samt"] + samt, 2)

    hsn_data = []
    for idx, (hsn_code, rec) in enumerate(hsn_dict.items(), 1):
        rec["num"] = idx
        hsn_data.append(rec)

    # Documents Issued
    doc_det = []
    if sales_invoices:
        sorted_invs = sorted(sales_invoices, key=lambda x: str(x.get("invoice_number", "")))
        first_inv = str(sorted_invs[0].get("invoice_number", "INV-01"))
        last_inv = str(sorted_invs[-1].get("invoice_number", "INV-01"))
        total_count = len(sorted_invs)
        doc_det.append({
            "doc_num": 1,
            "doc_typ": "Invoices for outward supply",
            "docs": [
                {
                    "num": 1,
                    "from": first_inv,
                    "to": last_inv,
                    "totnum": total_count,
                    "canc": 0,
                    "net_issue": total_count
                }
            ]
        })

    gstr1_payload = {
        "gstin": gstin,
        "fp": fp,
        "version": "GST1.0",
        "hash": "hash",
        "gt": round(total_taxable_all, 2),
        "cur_gt": round(total_taxable_all, 2),
        "b2b": b2b_formatted,
        "b2cs": b2cs_list,
        "hsn": {
            "data": hsn_data
        },
        "doc_issue": {
            "doc_det": doc_det
        }
    }

    return json.dumps(gstr1_payload, indent=2)

def generate_gstr3b_json(
    company: Dict[str, Any],
    sales_invoices: List[Dict[str, Any]],
    purchase_bills: List[Dict[str, Any]],
    period_month: Optional[str] = None,
    period_fy: Optional[str] = None
) -> str:
    """
    Generates official GSTN Offline Tool compliant GSTR-3B JSON
    for direct upload to https://services.gst.gov.in
    """
    gstin = company.get("gstin", "24MVMPS3622M1ZT")
    ret_period = get_return_period_fp(period_month, period_fy, sales_invoices or purchase_bills)

    tot_txval = sum(float(inv.get("taxable_amount", 0.0)) for inv in sales_invoices)
    tot_camt = sum(float(inv.get("cgst_amount", 0.0)) for inv in sales_invoices)
    tot_samt = sum(float(inv.get("sgst_amount", 0.0)) for inv in sales_invoices)
    tot_iamt = sum(float(inv.get("igst_amount", 0.0)) for inv in sales_invoices)

    eligible_bills = [b for b in purchase_bills if b.get("itc_eligibility") == "ELIGIBLE" and b.get("itc_claimed", 1) == 1]
    itc_camt = sum(float(b.get("cgst_amount", 0.0)) for b in eligible_bills)
    itc_samt = sum(float(b.get("sgst_amount", 0.0)) for b in eligible_bills)
    itc_iamt = sum(float(b.get("igst_amount", 0.0)) for b in eligible_bills)

    ineligible_bills = [b for b in purchase_bills if b.get("itc_eligibility") == "INELIGIBLE_17_5"]
    inelg_camt = sum(float(b.get("cgst_amount", 0.0)) for b in ineligible_bills)
    inelg_samt = sum(float(b.get("sgst_amount", 0.0)) for b in ineligible_bills)
    inelg_iamt = sum(float(b.get("igst_amount", 0.0)) for b in ineligible_bills)

    gstr3b_payload = {
        "gstin": gstin,
        "ret_period": ret_period,
        "filing_typ": "REG",
        "sec_sum": {
            "sec_nm": "GSTR3B",
            "tot_sections": 3
        },
        "sup_details": {
            "osup_det": {
                "txval": round(tot_txval, 2),
                "iamt": round(tot_iamt, 2),
                "camt": round(tot_camt, 2),
                "samt": round(tot_samt, 2),
                "csamt": 0.0
            },
            "osup_zero": {"txval": 0.0, "iamt": 0.0, "csamt": 0.0},
            "osup_nil_exmp": {"txval": 0.0},
            "isup_rev": {"txval": 0.0, "iamt": 0.0, "camt": 0.0, "samt": 0.0, "csamt": 0.0},
            "osup_nongst": {"txval": 0.0}
        },
        "itc_elg": {
            "itc_avl": [
                {"ty": "IMPG", "iamt": 0.0, "csamt": 0.0},
                {"ty": "IMPS", "iamt": 0.0, "csamt": 0.0},
                {"ty": "ISRC", "iamt": 0.0, "camt": 0.0, "samt": 0.0, "csamt": 0.0},
                {"ty": "ISD", "iamt": 0.0, "camt": 0.0, "samt": 0.0, "csamt": 0.0},
                {
                    "ty": "OTH",
                    "iamt": round(itc_iamt, 2),
                    "camt": round(itc_camt, 2),
                    "samt": round(itc_samt, 2),
                    "csamt": 0.0
                }
            ],
            "itc_rev": [
                {"ty": "RUL", "iamt": 0.0, "camt": 0.0, "samt": 0.0, "csamt": 0.0},
                {"ty": "OTH", "iamt": 0.0, "camt": 0.0, "samt": 0.0, "csamt": 0.0}
            ],
            "itc_net": {
                "iamt": round(itc_iamt, 2),
                "camt": round(itc_camt, 2),
                "samt": round(itc_samt, 2),
                "csamt": 0.0
            },
            "itc_inelg": [
                {
                    "ty": "RUL",
                    "iamt": round(inelg_iamt, 2),
                    "camt": round(inelg_camt, 2),
                    "samt": round(inelg_samt, 2),
                    "csamt": 0.0
                },
                {"ty": "OTH", "iamt": 0.0, "camt": 0.0, "samt": 0.0, "csamt": 0.0}
            ]
        }
    }

    return json.dumps(gstr3b_payload, indent=2)
