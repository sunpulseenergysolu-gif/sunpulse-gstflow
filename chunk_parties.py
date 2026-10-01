target_js = r"C:\Users\One Click Solution\.gemini\antigravity\scratch\gst-invoicing-app\static\app.js"

code = """
// ----------------- PARTIES (CUSTOMERS & VENDORS) -----------------
async function loadParties() {
  try {
    const res = await fetch("/api/parties");
    const data = await res.json();
    allParties = data.parties || [];

    const tbody = document.getElementById("partiesTbody");
    if (!tbody) return;
    tbody.innerHTML = "";

    allParties.forEach(p => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-50 transition";
      tr.innerHTML = `
        <td class="py-3 px-4 font-bold text-slate-800">${p.name}</td>
        <td class="py-3 px-4"><span class="px-2 py-0.5 rounded text-[10px] font-semibold ${p.type === 'CUSTOMER' ? 'bg-sky-100 text-sky-700' : 'bg-emerald-100 text-emerald-700'}">${p.type}</span></td>
        <td class="py-3 px-4 font-mono text-[11px] text-slate-600">${p.gstin || 'Unregistered'}</td>
        <td class="py-3 px-4 text-slate-600">${p.state} (${p.state_code})</td>
        <td class="py-3 px-4 text-slate-500">${p.phone || ''} ${p.email ? '<br/>' + p.email : ''}</td>
        <td class="py-3 px-4 text-slate-500 truncate max-w-xs">${p.billing_address || '-'}</td>
        <td class="py-3 px-4 text-center">
          <button onclick="deleteParty(${p.id})" class="text-slate-400 hover:text-rose-600 p-1"><i data-lucide="trash-2" class="w-4 h-4"></i></button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    lucide.createIcons();
  } catch (err) {
    console.error("Error loading parties", err);
  }
}

function openNewPartyModal() {
  document.getElementById("newPartyForm").reset();
  document.getElementById("newPartyModal").classList.remove("hidden");
  lucide.createIcons();
}

function closeNewPartyModal() {
  document.getElementById("newPartyModal").classList.add("hidden");
}

function autoDetectPartyState() {
  const gstin = document.getElementById("partyGstinInput").value;
  const code = getStateCodeFromGstin(gstin);
  if (code) {
    const found = stateCodes.find(s => s.code === code);
    if (found) {
      document.getElementById("partyStateInput").value = `${found.code} - ${found.name}`;
    }
  }
}

async function handleCreateParty(e) {
  e.preventDefault();
  const stateVal = document.getElementById("partyStateInput").value;
  const stateCode = stateVal.split(" - ")[0].trim();
  const stateName = stateVal.split(" - ")[1]?.trim() || stateVal;

  const payload = {
    name: document.getElementById("partyNameInput").value.trim(),
    type: document.getElementById("partyTypeInput").value,
    gstin: document.getElementById("partyGstinInput").value.trim(),
    state: stateName,
    state_code: stateCode,
    phone: document.getElementById("partyPhoneInput").value.trim(),
    email: document.getElementById("partyEmailInput").value.trim(),
    billing_address: document.getElementById("partyAddressInput").value.trim()
  };

  try {
    await fetch("/api/parties", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    closeNewPartyModal();
    await loadParties();
  } catch (err) {
    console.error("Error creating party", err);
  }
}

async function deleteParty(partyId) {
  if (!confirm("Are you sure you want to delete this party?")) return;
  try {
    await fetch(`/api/parties/${partyId}`, { method: "DELETE" });
    await loadParties();
  } catch (err) {
    console.error("Error deleting party", err);
  }
}

// ----------------- INVENTORY & ITEMS -----------------
async function loadItems() {
  try {
    const res = await fetch("/api/items");
    const data = await res.json();
    allItems = data.items || [];

    const tbody = document.getElementById("itemsTbody");
    if (!tbody) return;
    tbody.innerHTML = "";

    allItems.forEach(it => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-50 transition";
      tr.innerHTML = `
        <td class="py-3 px-4 font-bold text-slate-800">${it.name}</td>
        <td class="py-3 px-4 font-mono text-slate-600">${it.hsn_code || '-'}</td>
        <td class="py-3 px-4 text-center">${it.uom}</td>
        <td class="py-3 px-4 text-right font-bold text-slate-900">₹ ${it.selling_price.toFixed(2)}</td>
        <td class="py-3 px-4 text-right text-slate-600">₹ ${it.purchase_price.toFixed(2)}</td>
        <td class="py-3 px-4 text-center font-semibold text-indigo-600">${it.gst_rate}%</td>
        <td class="py-3 px-4 text-center font-bold text-slate-700">${it.stock_quantity}</td>
        <td class="py-3 px-4 text-center">
          <button onclick="deleteItem(${it.id})" class="text-slate-400 hover:text-rose-600 p-1"><i data-lucide="trash-2" class="w-4 h-4"></i></button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    lucide.createIcons();
  } catch (err) {
    console.error("Error loading items", err);
  }
}

function openNewItemModal() {
  document.getElementById("newItemForm").reset();
  document.getElementById("newItemModal").classList.remove("hidden");
  lucide.createIcons();
}

function closeNewItemModal() {
  document.getElementById("newItemModal").classList.add("hidden");
}

async function handleCreateItem(e) {
  e.preventDefault();
  const payload = {
    name: document.getElementById("itemNameInput").value.trim(),
    hsn_code: document.getElementById("itemHsnInput").value.trim(),
    uom: document.getElementById("itemUomInput").value,
    selling_price: parseFloat(document.getElementById("itemSellingPrice").value) || 0,
    gst_rate: parseFloat(document.getElementById("itemGstRate").value) || 18,
    purchase_price: 0,
    stock_quantity: 100
  };

  try {
    await fetch("/api/items", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    closeNewItemModal();
    await loadItems();
  } catch (err) {
    console.error("Error creating item", err);
  }
}

async function deleteItem(itemId) {
  if (!confirm("Are you sure you want to delete this item?")) return;
  try {
    await fetch(`/api/items/${itemId}`, { method: "DELETE" });
    await loadItems();
  } catch (err) {
    console.error("Error deleting item", err);
  }
}

// ----------------- COMPANY SETTINGS -----------------
async function loadCompanySettings() {
  try {
    const res = await fetch("/api/settings/company");
    const data = await res.json();
    const comp = data.company || {};

    document.getElementById("cfgName").value = comp.name || "";
    document.getElementById("cfgGstin").value = comp.gstin || "";
    document.getElementById("cfgStateCode").value = comp.state_code || "";
    if (comp.state && comp.state_code) {
      document.getElementById("cfgState").value = `${comp.state_code} - ${comp.state}`;
    }
    document.getElementById("cfgAddress").value = comp.address || "";
    document.getElementById("cfgCity").value = comp.city || "";
    document.getElementById("cfgPincode").value = comp.pincode || "";
    document.getElementById("cfgPhone").value = comp.phone || "";
    document.getElementById("cfgEmail").value = comp.email || "";

    document.getElementById("cfgBankName").value = comp.bank_name || "";
    document.getElementById("cfgBankAcc").value = comp.bank_acc || "";
    document.getElementById("cfgBankIfsc").value = comp.bank_ifsc || "";
    document.getElementById("cfgUpiId").value = comp.upi_id || "";
    document.getElementById("cfgPrefix").value = comp.invoice_prefix || "INV-";
    document.getElementById("cfgTerms").value = comp.invoice_terms || "";
  } catch (err) {
    console.error("Error loading settings", err);
  }
}

function autoDetectCompanyState() {
  const gstin = document.getElementById("cfgGstin").value;
  const code = getStateCodeFromGstin(gstin);
  if (code) {
    document.getElementById("cfgStateCode").value = code;
    const found = stateCodes.find(s => s.code === code);
    if (found) {
      document.getElementById("cfgState").value = `${found.code} - ${found.name}`;
    }
  }
}

function syncCompanyStateCode() {
  const stateVal = document.getElementById("cfgState").value;
  const code = stateVal.split(" - ")[0].trim();
  document.getElementById("cfgStateCode").value = code;
}

async function saveCompanySettings(e) {
  e.preventDefault();
  const stateVal = document.getElementById("cfgState").value;
  const stateCode = stateVal.split(" - ")[0].trim();
  const stateName = stateVal.split(" - ")[1]?.trim() || stateVal;

  const payload = {
    name: document.getElementById("cfgName").value.trim(),
    gstin: document.getElementById("cfgGstin").value.trim(),
    state: stateName,
    state_code: stateCode,
    address: document.getElementById("cfgAddress").value.trim(),
    city: document.getElementById("cfgCity").value.trim(),
    pincode: document.getElementById("cfgPincode").value.trim(),
    phone: document.getElementById("cfgPhone").value.trim(),
    email: document.getElementById("cfgEmail").value.trim(),
    bank_name: document.getElementById("cfgBankName").value.trim(),
    bank_acc: document.getElementById("cfgBankAcc").value.trim(),
    bank_ifsc: document.getElementById("cfgBankIfsc").value.trim(),
    upi_id: document.getElementById("cfgUpiId").value.trim(),
    invoice_prefix: document.getElementById("cfgPrefix").value.trim(),
    invoice_terms: document.getElementById("cfgTerms").value.trim()
  };

  try {
    const res = await fetch("/api/settings/company", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      alert("Company Settings Saved Successfully!");
      await loadDashboardData();
    }
  } catch (err) {
    console.error("Error saving company profile", err);
  }
}
"""

with open(target_js, "a", encoding="utf-8") as f:
    f.write(code)

print("Parties, Items, and Settings JS appended successfully")
