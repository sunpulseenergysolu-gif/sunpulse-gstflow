target_js = r"C:\Users\One Click Solution\.gemini\antigravity\scratch\gst-invoicing-app\static\app.js"

code = """
// ----------------- PURCHASE BILLS & ITC UPLOAD -----------------
async function loadPurchaseBills() {
  try {
    const res = await fetch("/api/purchases");
    const data = await res.json();
    allPurchases = data.bills || [];
    renderPurchaseTable(allPurchases);
  } catch (err) {
    console.error("Error loading purchase bills", err);
  }
}

function filterPurchases() {
  const search = document.getElementById("purchasesSearchInput").value.toLowerCase();
  const itcF = document.getElementById("purchasesItcFilter").value;

  const filtered = allPurchases.filter(b => {
    const matchSearch = (b.bill_number || "").toLowerCase().includes(search) ||
                        (b.vendor_name || "").toLowerCase().includes(search) ||
                        (b.vendor_gstin || "").toLowerCase().includes(search);
    const matchItc = (itcF === "ALL") || (b.itc_eligibility === itcF);
    return matchSearch && matchItc;
  });

  renderPurchaseTable(filtered);
}

function renderPurchaseTable(list) {
  const tbody = document.getElementById("purchaseBillsTbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" class="text-center py-8 text-slate-400">No purchase bills match your criteria</td></tr>`;
    return;
  }

  list.forEach(b => {
    const itcBadge = b.itc_eligibility === "ELIGIBLE"
      ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-700">🟢 Eligible ITC</span>`
      : `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-700">🔴 Blocked 17(5)</span>`;

    const totalGst = (b.cgst_amount || 0) + (b.sgst_amount || 0) + (b.igst_amount || 0);

    const docBtn = b.document_file
      ? `<button onclick="viewDocument('${b.document_file}', '${b.vendor_name}')" class="text-sky-600 hover:text-sky-800 font-semibold text-xs flex items-center gap-1 justify-center"><i data-lucide="file-text" class="w-3.5 h-3.5"></i> View Bill</button>`
      : `<span class="text-slate-400 text-[11px]">No File</span>`;

    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-50/80 transition";
    tr.innerHTML = `
      <td class="py-3 px-4 font-bold text-emerald-700 font-mono">${b.bill_number}</td>
      <td class="py-3 px-4 font-medium text-slate-800">${b.vendor_name}</td>
      <td class="py-3 px-4 font-mono text-[11px] text-slate-500">${b.vendor_gstin || 'Unregistered'}</td>
      <td class="py-3 px-4 text-slate-500">${b.bill_date}</td>
      <td class="py-3 px-4 text-right text-slate-600">₹ ${(b.taxable_amount || 0).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
      <td class="py-3 px-4 text-right font-bold text-emerald-600">₹ ${totalGst.toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
      <td class="py-3 px-4 text-right font-bold text-slate-900">₹ ${(b.total_amount || 0).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
      <td class="py-3 px-4 text-center">${itcBadge}</td>
      <td class="py-3 px-4 text-center">${docBtn}</td>
      <td class="py-3 px-4 text-center">
        <button onclick="deletePurchaseBill(${b.id})" title="Delete Bill" class="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition">
          <i data-lucide="trash-2" class="w-4 h-4"></i>
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  lucide.createIcons();
}

function openUploadBillModal() {
  document.getElementById("uploadBillForm").reset();
  const today = new Date().toISOString().split("T")[0];
  document.getElementById("billDate").value = today;
  document.getElementById("fileChosenLabel").innerText = "Click to upload or drag & drop Supplier Bill (PDF / JPG / PNG)";
  document.getElementById("uploadBillModal").classList.remove("hidden");
  lucide.createIcons();
}

function closeUploadBillModal() {
  document.getElementById("uploadBillModal").classList.add("hidden");
}

function handleFileChosen(input) {
  if (input.files && input.files[0]) {
    document.getElementById("fileChosenLabel").innerText = `Selected: ${input.files[0].name}`;
  }
}

function calcBillPreview() {}

async function handleUploadBillSubmit(e) {
  e.preventDefault();

  const formData = new FormData();
  formData.append("vendor_name", document.getElementById("billVendorName").value.trim());
  formData.append("vendor_gstin", document.getElementById("billVendorGstin").value.trim());
  formData.append("bill_number", document.getElementById("billNumber").value.trim());
  formData.append("bill_date", document.getElementById("billDate").value);
  formData.append("taxable_amount", parseFloat(document.getElementById("billTaxable").value) || 0);
  formData.append("gst_rate", parseFloat(document.getElementById("billGstRate").value) || 18);
  formData.append("is_interstate", document.getElementById("billIsInterstate").checked);
  
  const itcRadio = document.querySelector("input[name='itcEligibility']:checked");
  formData.append("itc_eligibility", itcRadio ? itcRadio.value : "ELIGIBLE");
  formData.append("payment_status", document.getElementById("billPaymentStatus").value);
  formData.append("notes", document.getElementById("billNotes").value.trim());

  const fileInput = document.getElementById("billFileInput");
  if (fileInput.files && fileInput.files[0]) {
    formData.append("file", fileInput.files[0]);
  }

  try {
    const res = await fetch("/api/purchases/upload", {
      method: "POST",
      body: formData
    });

    if (res.ok) {
      closeUploadBillModal();
      await loadPurchaseBills();
      await loadDashboardData();
      alert("Purchase Bill & Input Tax Credit (ITC) recorded successfully!");
    } else {
      const err = await res.json();
      alert("Error: " + (err.detail || "Upload failed"));
    }
  } catch (err) {
    console.error("Failed to upload purchase bill", err);
  }
}

function viewDocument(filename, vendorName) {
  const frame = document.getElementById("docViewerFrame");
  frame.src = `/uploads/${filename}`;
  document.getElementById("docViewerTitle").innerText = `Bill Document - ${vendorName} (${filename})`;
  document.getElementById("viewDocumentModal").classList.remove("hidden");
  lucide.createIcons();
}

function closeDocumentModal() {
  document.getElementById("viewDocumentModal").classList.add("hidden");
  document.getElementById("docViewerFrame").src = "";
}

async function deletePurchaseBill(billId) {
  if (!confirm("Are you sure you want to delete this purchase bill?")) return;
  try {
    await fetch(`/api/purchases/${billId}`, { method: "DELETE" });
    await loadPurchaseBills();
    await loadDashboardData();
  } catch (err) {
    console.error("Error deleting bill", err);
  }
}
"""

with open(target_js, "a", encoding="utf-8") as f:
    f.write(code)

print("Purchase Bills JS appended successfully")
