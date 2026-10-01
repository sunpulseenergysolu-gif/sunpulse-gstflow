import os

target_js = r"C:\Users\One Click Solution\.gemini\antigravity\scratch\gst-invoicing-app\static\app.js"

part1 = """// GSTFlow Client-Side Application Engine
let stateCodes = [];
let companyProfile = {};
let allInvoices = [];
let allPurchases = [];
let allParties = [];
let allItems = [];
let currentInvoiceData = null;

// Initialization
document.addEventListener("DOMContentLoaded", async () => {
  await loadStateCodes();
  await loadDashboardData();
  await loadParties();
  await loadItems();
  
  const today = new Date().toISOString().split("T")[0];
  if (document.getElementById("invDate")) document.getElementById("invDate").value = today;
  if (document.getElementById("billDate")) document.getElementById("billDate").value = today;

  lucide.createIcons();
});

// ----------------- TAB NAVIGATION -----------------
function switchTab(tabId) {
  document.querySelectorAll(".tab-view").forEach(el => el.classList.add("hidden"));
  const target = document.getElementById(`tab-${tabId}`);
  if (target) target.classList.remove("hidden");

  document.querySelectorAll(".nav-btn").forEach(btn => {
    btn.className = "nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all text-slate-400 hover:text-white hover:bg-slate-800/60";
  });

  const activeBtn = document.getElementById(`nav-${tabId}`);
  if (activeBtn) {
    activeBtn.className = "nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all bg-sky-600/20 text-sky-400 border border-sky-500/30";
  }

  const titles = {
    "dashboard": "GST Overview & Input Tax Credit (ITC) Dashboard",
    "sales": "Sales Invoices (Outward Supplies)",
    "purchases": "Purchase Bills & ITC Upload Hub",
    "itc-ledger": "GST Credit (ITC) & Tax Set-off Ledger",
    "parties": "Customers & Vendors Directory",
    "inventory": "Products & Services (HSN Master)",
    "reports": "GSTR-1 & GSTR-3B Tax Filing Reports",
    "settings": "Company Profile & GST Configuration"
  };
  document.getElementById("topHeaderTitle").innerText = titles[tabId] || "GST Management";

  if (tabId === "dashboard") loadDashboardData();
  if (tabId === "sales") loadSalesInvoices();
  if (tabId === "purchases") loadPurchaseBills();
  if (tabId === "itc-ledger") loadDashboardData();
  if (tabId === "parties") loadParties();
  if (tabId === "inventory") loadItems();
  if (tabId === "settings") loadCompanySettings();

  lucide.createIcons();
}

// ----------------- STATE CODES & INITIAL LOOKUPS -----------------
async function loadStateCodes() {
  try {
    const res = await fetch("/api/state-codes");
    const data = await res.json();
    stateCodes = data.states || [];

    const dropdownIds = ["invPartyState", "cfgState", "partyStateInput"];
    dropdownIds.forEach(id => {
      const select = document.getElementById(id);
      if (!select) return;
      select.innerHTML = "";
      stateCodes.forEach(s => {
        const opt = document.createElement("option");
        opt.value = `${s.code} - ${s.name}`;
        opt.text = `${s.code} - ${s.name}`;
        select.appendChild(opt);
      });
    });
  } catch (err) {
    console.error("Failed to load state codes", err);
  }
}

function getStateCodeFromGstin(gstin) {
  if (gstin && gstin.trim().length >= 2) {
    return gstin.trim().substring(0, 2);
  }
  return "";
}

// ----------------- DASHBOARD & METRICS -----------------
async function loadDashboardData() {
  try {
    const res = await fetch("/api/dashboard");
    const data = await res.json();

    companyProfile = data.company || {};
    const metrics = data.metrics || {};
    const tax = data.tax_summary || {};
    const outputTax = tax.output_tax || {};
    const itc = tax.input_tax_credit || {};
    const net = tax.net_payable || {};
    const closing = tax.closing_credit_balance || {};

    if (document.getElementById("sidebarCompanyName")) {
      document.getElementById("sidebarCompanyName").innerText = companyProfile.name || "My Business";
    }
    if (document.getElementById("sidebarGstin")) {
      document.getElementById("sidebarGstin").innerText = companyProfile.gstin || "Unregistered";
    }

    document.getElementById("cardOutputTax").innerText = `₹ ${outputTax.total?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;
    document.getElementById("cardSalesCount").innerText = `${metrics.total_sales_count || 0} Invoices`;

    document.getElementById("cardInputTax").innerText = `₹ ${itc.total?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;
    document.getElementById("cardPurchaseCount").innerText = `${metrics.total_purchase_count || 0} Bills`;

    const netPayableVal = net.total || 0;
    const closingCreditVal = closing.total || 0;

    if (netPayableVal > 0) {
      document.getElementById("cardNetLabel").innerText = "Net GST Payable";
      document.getElementById("cardNetPayable").innerText = `₹ ${netPayableVal.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
      document.getElementById("cardNetPayable").className = "text-2xl font-extrabold text-rose-600 mt-3";
      document.getElementById("cardNetSubtext").innerText = "Liability to Pay to Govt";
      document.getElementById("cardNetSubtext").className = "text-rose-600 font-semibold";
      document.getElementById("cardNetBar").className = "absolute bottom-0 left-0 right-0 h-1 bg-rose-500";
    } else {
      document.getElementById("cardNetLabel").innerText = "ITC Carry Forward";
      document.getElementById("cardNetPayable").innerText = `₹ ${closingCreditVal.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
      document.getElementById("cardNetPayable").className = "text-2xl font-extrabold text-emerald-600 mt-3";
      document.getElementById("cardNetSubtext").innerText = "Credit Balance Available";
      document.getElementById("cardNetSubtext").className = "text-emerald-600 font-semibold";
      document.getElementById("cardNetBar").className = "absolute bottom-0 left-0 right-0 h-1 bg-emerald-500";
    }

    document.getElementById("cardTotalSales").innerText = `₹ ${metrics.total_sales_value?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;
    document.getElementById("cardReceivables").innerText = `₹ ${metrics.receivables?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0'} Due`;

    document.getElementById("poolCgstOutput").innerText = `₹ ${outputTax.cgst?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;
    document.getElementById("poolCgstInput").innerText = `₹ ${itc.cgst?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;
    document.getElementById("poolCgstNet").innerText = `₹ ${net.cgst?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;

    document.getElementById("poolSgstOutput").innerText = `₹ ${outputTax.sgst?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;
    document.getElementById("poolSgstInput").innerText = `₹ ${itc.sgst?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;
    document.getElementById("poolSgstNet").innerText = `₹ ${net.sgst?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;

    document.getElementById("poolIgstOutput").innerText = `₹ ${outputTax.igst?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;
    document.getElementById("poolIgstInput").innerText = `₹ ${itc.igst?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;
    document.getElementById("poolIgstNet").innerText = `₹ ${net.igst?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;

    if (document.getElementById("ledgerOutwardTotal")) {
      document.getElementById("ledgerOutwardTotal").innerText = `₹ ${outputTax.total?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;
      document.getElementById("ledgerOutwardCgst").innerText = `₹ ${outputTax.cgst?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;
      document.getElementById("ledgerOutwardSgst").innerText = `₹ ${outputTax.sgst?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;
      document.getElementById("ledgerOutwardIgst").innerText = `₹ ${outputTax.igst?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;

      document.getElementById("ledgerItcTotal").innerText = `₹ ${itc.total?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;
      document.getElementById("ledgerItcCgst").innerText = `₹ ${itc.cgst?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;
      document.getElementById("ledgerItcSgst").innerText = `₹ ${itc.sgst?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;
      document.getElementById("ledgerItcIgst").innerText = `₹ ${itc.igst?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;

      document.getElementById("ledgerBlockedItc").innerText = `₹ ${itc.blocked_itc?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;

      document.getElementById("ledgerNetPayableTotal").innerText = `₹ ${net.total?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;
      document.getElementById("ledgerNetCgst").innerText = `₹ ${net.cgst?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;
      document.getElementById("ledgerNetSgst").innerText = `₹ ${net.sgst?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;
      document.getElementById("ledgerNetIgst").innerText = `₹ ${net.igst?.toLocaleString('en-IN', {minimumFractionDigits: 2}) || '0.00'}`;
    }

    renderRecentActivity(data.recent_activity || []);
    lucide.createIcons();
  } catch (err) {
    console.error("Error loading dashboard data", err);
  }
}

function renderRecentActivity(list) {
  const tbody = document.getElementById("recentActivityTbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-6 text-slate-400">No recent transactions recorded</td></tr>`;
    return;
  }

  list.forEach(item => {
    const isSale = item.type === "SALE";
    const typeBadge = isSale 
      ? `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-sky-100 text-sky-700">Sale</span>`
      : `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-700">Purchase</span>`;

    const statusBadge = item.status === "PAID"
      ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-700">Paid</span>`
      : item.status === "PARTIAL"
      ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-700">Partial</span>`
      : `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-700">Unpaid</span>`;

    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-50 transition";
    tr.innerHTML = `
      <td class="py-3 px-4">${typeBadge}</td>
      <td class="py-3 px-4 font-bold text-slate-800">${item.number}</td>
      <td class="py-3 px-4 text-slate-700">${item.party}</td>
      <td class="py-3 px-4 text-slate-500">${item.date}</td>
      <td class="py-3 px-4 text-right font-medium text-slate-600">₹ ${item.tax.toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
      <td class="py-3 px-4 text-right font-bold text-slate-900">₹ ${item.amount.toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
      <td class="py-3 px-4 text-center">${statusBadge}</td>
      <td class="py-3 px-4 text-center text-slate-500 text-[11px]">${item.tag}</td>
    `;
    tbody.appendChild(tr);
  });
}
"""

with open(target_js, "w", encoding="utf-8") as f:
    f.write(part1)

print("Part 1 of app.js written successfully")
