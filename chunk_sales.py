target_js = r"C:\Users\One Click Solution\.gemini\antigravity\scratch\gst-invoicing-app\static\app.js"

code = """
// ----------------- SALES INVOICES -----------------
async function loadSalesInvoices() {
  try {
    const res = await fetch("/api/invoices");
    const data = await res.json();
    allInvoices = data.invoices || [];
    renderSalesTable(allInvoices);
  } catch (err) {
    console.error("Error loading sales invoices", err);
  }
}

function filterSales() {
  const search = document.getElementById("salesSearchInput").value.toLowerCase();
  const typeF = document.getElementById("salesTypeFilter").value;
  const statusF = document.getElementById("salesStatusFilter").value;

  const filtered = allInvoices.filter(inv => {
    const matchSearch = (inv.invoice_number || "").toLowerCase().includes(search) ||
                        (inv.party_name || "").toLowerCase().includes(search) ||
                        (inv.party_gstin || "").toLowerCase().includes(search);
    const matchType = (typeF === "ALL") || (inv.invoice_type === typeF);
    const matchStatus = (statusF === "ALL") || (inv.payment_status === statusF);
    return matchSearch && matchType && matchStatus;
  });

  renderSalesTable(filtered);
}

function renderSalesTable(list) {
  const tbody = document.getElementById("salesInvoicesTbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" class="text-center py-8 text-slate-400">No invoices match your criteria</td></tr>`;
    return;
  }

  list.forEach(inv => {
    const statusBadge = inv.payment_status === "PAID"
      ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-700">Paid</span>`
      : inv.payment_status === "PARTIAL"
      ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-700">Partial</span>`
      : `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-700">Unpaid</span>`;

    const totalGst = (inv.cgst_amount || 0) + (inv.sgst_amount || 0) + (inv.igst_amount || 0);

    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-50/80 transition";
    tr.innerHTML = `
      <td class="py-3 px-4 font-bold text-sky-700 font-mono">${inv.invoice_number}</td>
      <td class="py-3 px-4"><span class="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">${inv.invoice_type}</span></td>
      <td class="py-3 px-4 font-medium text-slate-800">${inv.party_name}</td>
      <td class="py-3 px-4 font-mono text-[11px] text-slate-500">${inv.party_gstin || 'Unregistered'}</td>
      <td class="py-3 px-4 text-slate-500">${inv.invoice_date}</td>
      <td class="py-3 px-4 text-right text-slate-600">₹ ${(inv.taxable_amount || 0).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
      <td class="py-3 px-4 text-right font-medium text-indigo-600">₹ ${totalGst.toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
      <td class="py-3 px-4 text-right font-bold text-slate-900">₹ ${(inv.total_amount || 0).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
      <td class="py-3 px-4 text-center">${statusBadge}</td>
      <td class="py-3 px-4 text-center">
        <div class="flex items-center justify-center gap-1.5">
          <button onclick="viewInvoiceDetail(${inv.id})" title="View / Print Tax Invoice" class="p-1.5 text-slate-600 hover:text-sky-600 hover:bg-sky-50 rounded-lg transition">
            <i data-lucide="eye" class="w-4 h-4"></i>
          </button>
          <a href="/api/invoices/${inv.id}/pdf" target="_blank" title="Download PDF" class="p-1.5 text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition">
            <i data-lucide="download" class="w-4 h-4"></i>
          </a>
          <button onclick="deleteInvoice(${inv.id})" title="Delete Invoice" class="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition">
            <i data-lucide="trash-2" class="w-4 h-4"></i>
          </button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });

  lucide.createIcons();
}
"""

with open(target_js, "a", encoding="utf-8") as f:
    f.write(code)

print("Chunk Sales appended successfully")
