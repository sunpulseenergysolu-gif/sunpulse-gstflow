target_js = r"C:\Users\One Click Solution\.gemini\antigravity\scratch\gst-invoicing-app\static\app.js"

code = """
async function viewInvoiceDetail(invId) {
  try {
    const res = await fetch(`/api/invoices/${invId}`);
    const data = await res.json();
    currentInvoiceData = data;

    const inv = data.invoice;
    const items = data.items || [];
    const comp = data.company || {};

    document.getElementById("viewInvNumberTitle").innerText = inv.invoice_number;
    document.getElementById("viewInvTypeTag").innerText = inv.invoice_type === "B2B" ? "TAX INVOICE" : "RETAIL INVOICE";
    document.getElementById("viewInvPdfDownloadBtn").href = `/api/invoices/${inv.id}/pdf`;

    const isInterstate = Boolean(inv.is_interstate);

    let itemsHtml = "";
    items.forEach((it, idx) => {
      const taxCol = isInterstate 
        ? `<td class="p-2 text-right">₹ ${it.igst_amount.toFixed(2)} (${it.igst_rate}%)</td>`
        : `<td class="p-2 text-right">₹ ${it.cgst_amount.toFixed(2)}</td><td class="p-2 text-right">₹ ${it.sgst_amount.toFixed(2)}</td>`;

      itemsHtml += `
        <tr class="border-b border-slate-200">
          <td class="p-2 text-center">${idx + 1}</td>
          <td class="p-2 font-bold">${it.item_name}</td>
          <td class="p-2 text-center font-mono">${it.hsn_code || '-'}</td>
          <td class="p-2 text-center">${it.quantity} ${it.uom}</td>
          <td class="p-2 text-right">₹ ${it.rate.toFixed(2)}</td>
          <td class="p-2 text-right">₹ ${it.taxable_value.toFixed(2)}</td>
          ${taxCol}
          <td class="p-2 text-right font-bold">₹ ${it.total.toFixed(2)}</td>
        </tr>
      `;
    });

    const taxHeader = isInterstate 
      ? `<th class="p-2 text-right">IGST</th>`
      : `<th class="p-2 text-right">CGST</th><th class="p-2 text-right">SGST</th>`;

    const printableHtml = `
      <div class="border border-slate-300 rounded-lg p-6 bg-white space-y-4">
        <div class="text-center border-b pb-3 border-slate-300">
          <h2 class="text-xl font-extrabold text-blue-900">${inv.invoice_type === 'B2B' ? 'TAX INVOICE' : 'BILL OF SUPPLY / INVOICE'}</h2>
          <p class="text-[10px] text-slate-500">(Issued under Central Goods and Services Tax Rules, 2017)</p>
        </div>

        <div class="grid grid-cols-2 gap-4 text-xs border border-slate-200 p-3 rounded-lg bg-slate-50">
          <div>
            <p class="font-bold text-sm text-blue-900">${comp.name || 'Bharat Tech Solutions'}</p>
            <p>${comp.address || ''}, ${comp.city || ''} - ${comp.pincode || ''}</p>
            <p><b>GSTIN:</b> <span class="font-mono">${comp.gstin || ''}</span> | <b>State:</b> ${comp.state || ''} (${comp.state_code || ''})</p>
            <p><b>Phone:</b> ${comp.phone || ''} | <b>Email:</b> ${comp.email || ''}</p>
          </div>
          <div class="text-right space-y-0.5">
            <p><b>Invoice No:</b> <span class="font-bold font-mono text-blue-900">${inv.invoice_number}</span></p>
            <p><b>Invoice Date:</b> ${inv.invoice_date}</p>
            <p><b>Due Date:</b> ${inv.due_date || 'Immediate'}</p>
            <p><b>Place of Supply:</b> ${inv.place_of_supply}</p>
          </div>
        </div>

        <div class="border border-slate-200 p-3 rounded-lg grid grid-cols-2 gap-4 text-xs">
          <div>
            <p class="font-bold text-slate-700">Billed To (Customer Details):</p>
            <p class="font-bold text-sm text-slate-900">${inv.party_name}</p>
            <p><b>Address:</b> ${inv.party_address || 'N/A'}</p>
            <p><b>GSTIN / UIN:</b> ${inv.party_gstin || 'Unregistered (B2C)'}</p>
            <p><b>State:</b> ${inv.party_state} (Code: ${inv.party_state_code})</p>
          </div>
          <div>
            <p class="font-bold text-slate-700">Shipped To (Delivery Address):</p>
            <p class="font-bold text-slate-900">${inv.party_name}</p>
            <p>${inv.shipping_address || inv.party_address || 'Same as billing address'}</p>
            <p><b>Place of Supply:</b> ${inv.place_of_supply}</p>
          </div>
        </div>

        <table class="w-full text-left text-xs border border-slate-200">
          <thead class="bg-blue-900 text-white font-semibold">
            <tr>
              <th class="p-2 text-center w-8">#</th>
              <th class="p-2">Item Description</th>
              <th class="p-2 text-center">HSN</th>
              <th class="p-2 text-center">Qty</th>
              <th class="p-2 text-right">Rate</th>
              <th class="p-2 text-right">Taxable</th>
              ${taxHeader}
              <th class="p-2 text-right">Total</th>
            </tr>
          </thead>
          <tbody>
            ${itemsHtml}
          </tbody>
        </table>

        <div class="grid grid-cols-2 gap-4 text-xs border border-slate-200 p-3 rounded-lg bg-slate-50">
          <div>
            <p class="font-bold text-slate-700 mb-1">Bank Account Details:</p>
            <p><b>Bank:</b> ${comp.bank_name || 'HDFC Bank Ltd'}</p>
            <p><b>A/C No:</b> <span class="font-mono">${comp.bank_acc || '50200012345678'}</span></p>
            <p><b>IFSC Code:</b> <span class="font-mono">${comp.bank_ifsc || 'HDFC0000123'}</span></p>
            <p><b>UPI ID:</b> <span class="font-mono">${comp.upi_id || 'bharattech@okhdfcbank'}</span></p>
          </div>

          <div class="text-right space-y-1">
            <div class="flex justify-between"><span>Taxable Amount:</span><span>₹ ${(inv.taxable_amount || 0).toFixed(2)}</span></div>
            ${isInterstate ? `<div class="flex justify-between"><span>Integrated Tax (IGST):</span><span>₹ ${(inv.igst_amount || 0).toFixed(2)}</span></div>` : `
              <div class="flex justify-between"><span>Central Tax (CGST):</span><span>₹ ${(inv.cgst_amount || 0).toFixed(2)}</span></div>
              <div class="flex justify-between"><span>State Tax (SGST):</span><span>₹ ${(inv.sgst_amount || 0).toFixed(2)}</span></div>
            `}
            <div class="pt-2 border-t font-bold text-sm text-blue-900 flex justify-between">
              <span>Total Invoice Amount:</span><span>₹ ${(inv.total_amount || 0).toFixed(2)}</span>
            </div>
          </div>
        </div>

        <p class="text-xs"><b>Amount in Words:</b> <i>${inv.amount_in_words || ''}</i></p>

        <div class="pt-3 border-t border-slate-200 flex justify-between text-[11px] text-slate-600">
          <div>
            <p class="font-bold">Terms & Conditions:</p>
            <p class="whitespace-pre-line text-[10px] text-slate-500">${comp.invoice_terms || '1. Goods once sold will not be returned. 2. Subject to local jurisdiction.'}</p>
          </div>
          <div class="text-right">
            <p>For <b>${comp.name || 'Company'}</b></p>
            <br/><br/>
            <p class="font-bold">Authorized Signatory</p>
          </div>
        </div>
      </div>
    `;

    document.getElementById("printableInvoice").innerHTML = printableHtml;
    document.getElementById("viewInvoiceModal").classList.remove("hidden");
    lucide.createIcons();
  } catch (err) {
    console.error("Error viewing invoice", err);
  }
}

function closeViewInvoiceModal() {
  document.getElementById("viewInvoiceModal").classList.add("hidden");
}

function printCurrentInvoice() {
  window.print();
}

async function deleteInvoice(invId) {
  if (!confirm("Are you sure you want to delete this invoice?")) return;
  try {
    await fetch(`/api/invoices/${invId}`, { method: "DELETE" });
    await loadSalesInvoices();
    await loadDashboardData();
  } catch (err) {
    console.error("Error deleting invoice", err);
  }
}
"""

with open(target_js, "a", encoding="utf-8") as f:
    f.write(code)

print("Invoice Viewer & Printable JS appended successfully")
