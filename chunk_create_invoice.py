target_js = r"C:\Users\One Click Solution\.gemini\antigravity\scratch\gst-invoicing-app\static\app.js"

code = """
// ----------------- CREATE INVOICE -----------------
function openNewInvoiceModal() {
  document.getElementById("newInvoiceForm").reset();
  const today = new Date().toISOString().split("T")[0];
  document.getElementById("invDate").value = today;

  const tbody = document.getElementById("invoiceItemsTbody");
  tbody.innerHTML = "";
  addInvoiceLineRow();

  const custSelect = document.getElementById("invCustomerSelect");
  custSelect.innerHTML = `<option value="">-- Choose Existing Customer --</option>`;
  allParties.filter(p => p.type === "CUSTOMER" || p.type === "BOTH").forEach(p => {
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.text = `${p.name} (${p.gstin || 'B2C'})`;
    custSelect.appendChild(opt);
  });

  recalculateInvoiceLineItems();
  document.getElementById("newInvoiceModal").classList.remove("hidden");
  lucide.createIcons();
}

function closeNewInvoiceModal() {
  document.getElementById("newInvoiceModal").classList.add("hidden");
}

function handleCustomerSelect() {
  const custId = document.getElementById("invCustomerSelect").value;
  if (!custId) return;

  const party = allParties.find(p => p.id == custId);
  if (party) {
    document.getElementById("invPartyName").value = party.name;
    document.getElementById("invPartyGstin").value = party.gstin || "";
    document.getElementById("invPartyAddress").value = party.billing_address || "";
    
    if (party.state && party.state_code) {
      document.getElementById("invPartyState").value = `${party.state_code} - ${party.state}`;
    }
    recalculateInvoiceLineItems();
  }
}

function autoDetectBuyerStateFromGstin() {
  const gstin = document.getElementById("invPartyGstin").value;
  const code = getStateCodeFromGstin(gstin);
  if (code) {
    const found = stateCodes.find(s => s.code === code);
    if (found) {
      document.getElementById("invPartyState").value = `${found.code} - ${found.name}`;
      recalculateInvoiceLineItems();
    }
  }
}

function addInvoiceLineRow() {
  const tbody = document.getElementById("invoiceItemsTbody");
  const rowId = `item_row_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`;

  const tr = document.createElement("tr");
  tr.id = rowId;
  tr.className = "hover:bg-slate-50/50";

  let itemOptions = `<option value="">-- Select product --</option>`;
  allItems.forEach(it => {
    itemOptions += `<option value="${it.id}" data-name="${it.name}" data-hsn="${it.hsn_code || ''}" data-uom="${it.uom}" data-price="${it.selling_price}" data-gst="${it.gst_rate}">${it.name} (₹${it.selling_price})</option>`;
  });

  tr.innerHTML = `
    <td class="py-2 px-3">
      <select onchange="onItemDropdownChange('${rowId}', this)" class="w-full text-xs p-1.5 rounded border border-slate-200 mb-1">
        ${itemOptions}
      </select>
      <input type="text" placeholder="Item Name" class="item-name w-full text-xs p-1.5 rounded border border-slate-200" required />
    </td>
    <td class="py-2 px-2">
      <input type="text" placeholder="HSN" class="item-hsn w-full text-xs p-1.5 rounded border border-slate-200 font-mono" />
    </td>
    <td class="py-2 px-2">
      <input type="number" step="any" value="1" min="0.01" oninput="recalculateInvoiceLineItems()" class="item-qty w-full text-xs p-1.5 rounded border border-slate-200 text-center" required />
    </td>
    <td class="py-2 px-2">
      <input type="text" value="Pcs" class="item-uom w-full text-xs p-1.5 rounded border border-slate-200 text-center" />
    </td>
    <td class="py-2 px-2">
      <input type="number" step="any" value="0" min="0" oninput="recalculateInvoiceLineItems()" class="item-rate w-full text-xs p-1.5 rounded border border-slate-200 text-right font-semibold" required />
    </td>
    <td class="py-2 px-2">
      <select onchange="recalculateInvoiceLineItems()" class="item-gst w-full text-xs p-1.5 rounded border border-slate-200 text-center">
        <option value="18" selected>18%</option>
        <option value="12">12%</option>
        <option value="5">5%</option>
        <option value="28">28%</option>
        <option value="0">0%</option>
      </select>
    </td>
    <td class="py-2 px-3 text-right">
      <span class="item-total-display font-bold text-slate-800">₹ 0.00</span>
    </td>
    <td class="py-2 px-2 text-center">
      <button type="button" onclick="removeInvoiceLineRow('${rowId}')" class="text-slate-400 hover:text-rose-600 p-1">
        <i data-lucide="trash" class="w-3.5 h-3.5"></i>
      </button>
    </td>
  `;

  tbody.appendChild(tr);
  lucide.createIcons();
  recalculateInvoiceLineItems();
}

function onItemDropdownChange(rowId, selectEl) {
  const row = document.getElementById(rowId);
  if (!row) return;

  const selectedOpt = selectEl.options[selectEl.selectedIndex];
  if (selectedOpt && selectedOpt.value) {
    row.querySelector(".item-name").value = selectedOpt.getAttribute("data-name") || "";
    row.querySelector(".item-hsn").value = selectedOpt.getAttribute("data-hsn") || "";
    row.querySelector(".item-uom").value = selectedOpt.getAttribute("data-uom") || "Pcs";
    row.querySelector(".item-rate").value = selectedOpt.getAttribute("data-price") || 0;
    row.querySelector(".item-gst").value = selectedOpt.getAttribute("data-gst") || 18;
  }
  recalculateInvoiceLineItems();
}

function removeInvoiceLineRow(rowId) {
  const tbody = document.getElementById("invoiceItemsTbody");
  if (tbody.children.length <= 1) {
    alert("At least one line item is required!");
    return;
  }
  const row = document.getElementById(rowId);
  if (row) row.remove();
  recalculateInvoiceLineItems();
}

function recalculateInvoiceLineItems() {
  const sellerStateCode = (companyProfile.state_code || "27").trim().padStart(2, "0");
  const buyerStateVal = document.getElementById("invPartyState")?.value || "";
  const buyerStateCode = buyerStateVal.split(" - ")[0].trim().padStart(2, "0");

  const isInterstate = (sellerStateCode !== buyerStateCode);

  const badge = document.getElementById("invTaxTypeBadge");
  const cgstRow = document.getElementById("invCgstRow");
  const sgstRow = document.getElementById("invSgstRow");
  const igstRow = document.getElementById("invIgstRow");

  if (isInterstate) {
    badge.innerText = `Inter-State Supply (IGST Applicable)`;
    badge.className = "text-xs font-bold text-purple-400";
    cgstRow.classList.add("hidden");
    sgstRow.classList.add("hidden");
    igstRow.classList.remove("hidden");
  } else {
    badge.innerText = `Intra-State Supply (CGST + SGST Applicable)`;
    badge.className = "text-xs font-bold text-sky-400";
    cgstRow.classList.remove("hidden");
    sgstRow.classList.remove("hidden");
    igstRow.classList.add("hidden");
  }

  let totalTaxable = 0;
  let totalCgst = 0;
  let totalSgst = 0;
  let totalIgst = 0;

  const rows = document.querySelectorAll("#invoiceItemsTbody tr");
  rows.forEach(row => {
    const qty = parseFloat(row.querySelector(".item-qty")?.value) || 0;
    const rate = parseFloat(row.querySelector(".item-rate")?.value) || 0;
    const gstRate = parseFloat(row.querySelector(".item-gst")?.value) || 0;

    const taxable = qty * rate;
    const taxAmt = (taxable * gstRate) / 100.0;
    const rowTotal = taxable + taxAmt;

    totalTaxable += taxable;

    if (isInterstate) {
      totalIgst += taxAmt;
    } else {
      totalCgst += taxAmt / 2.0;
      totalSgst += taxAmt / 2.0;
    }

    const disp = row.querySelector(".item-total-display");
    if (disp) disp.innerText = `₹ ${rowTotal.toFixed(2)}`;
  });

  const grandTotal = Math.round(totalTaxable + totalCgst + totalSgst + totalIgst);

  document.getElementById("invTaxableSubtotal").innerText = `₹ ${totalTaxable.toFixed(2)}`;
  document.getElementById("invCgstTotal").innerText = `₹ ${totalCgst.toFixed(2)}`;
  document.getElementById("invSgstTotal").innerText = `₹ ${totalSgst.toFixed(2)}`;
  document.getElementById("invIgstTotal").innerText = `₹ ${totalIgst.toFixed(2)}`;
  document.getElementById("invGrandTotal").innerText = `₹ ${grandTotal.toFixed(2)}`;
  document.getElementById("invWordsPreview").innerText = `Grand Total: ₹ ${grandTotal.toLocaleString('en-IN')}`;
}

async function handleCreateInvoiceSubmit(e) {
  e.preventDefault();

  const buyerStateVal = document.getElementById("invPartyState").value;
  const buyerStateCode = buyerStateVal.split(" - ")[0].trim();
  const buyerStateName = buyerStateVal.split(" - ")[1]?.trim() || buyerStateVal;

  const items = [];
  document.querySelectorAll("#invoiceItemsTbody tr").forEach(row => {
    const name = row.querySelector(".item-name").value.trim();
    if (!name) return;
    items.push({
      item_name: name,
      hsn_code: row.querySelector(".item-hsn").value.trim(),
      quantity: parseFloat(row.querySelector(".item-qty").value) || 1,
      uom: row.querySelector(".item-uom").value.trim() || "Pcs",
      rate: parseFloat(row.querySelector(".item-rate").value) || 0,
      discount_percent: 0,
      gst_rate: parseFloat(row.querySelector(".item-gst").value) || 18
    });
  });

  if (items.length === 0) {
    alert("Please add at least one valid invoice item!");
    return;
  }

  const payload = {
    invoice_number: document.getElementById("invNumber").value.trim(),
    invoice_type: document.getElementById("invType").value,
    invoice_date: document.getElementById("invDate").value,
    party_name: document.getElementById("invPartyName").value.trim(),
    party_gstin: document.getElementById("invPartyGstin").value.trim(),
    party_address: document.getElementById("invPartyAddress").value.trim(),
    shipping_address: document.getElementById("invPartyAddress").value.trim(),
    party_state: buyerStateName,
    party_state_code: buyerStateCode,
    items: items,
    payment_status: document.getElementById("invPaymentStatus").value,
    amount_paid: parseFloat(document.getElementById("invAmountPaid").value) || 0,
    payment_mode: document.getElementById("invPaymentMode").value,
    notes: document.getElementById("invNotes").value.trim()
  };

  try {
    const res = await fetch("/api/invoices", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      closeNewInvoiceModal();
      await loadSalesInvoices();
      await loadDashboardData();
      alert("Tax Invoice Created Successfully!");
    } else {
      const err = await res.json();
      alert("Error: " + (err.detail || "Failed to create invoice"));
    }
  } catch (err) {
    console.error("Failed to submit invoice", err);
  }
}
"""

with open(target_js, "a", encoding="utf-8") as f:
    f.write(code)

print("Invoice Creation JS appended successfully")
