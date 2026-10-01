import os

target_html = r"C:\Users\One Click Solution\.gemini\antigravity\scratch\gst-invoicing-app\static\index.html"

chunks = []

chunks.append("""
  <!-- ================= MODAL: CREATE NEW TAX INVOICE ================= -->
  <div id="newInvoiceModal" class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm hidden z-50 flex items-center justify-center p-4 overflow-y-auto">
    <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-4xl max-h-[92vh] flex flex-col overflow-hidden">
      
      <div class="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/80 shrink-0">
        <div>
          <h3 class="text-base font-bold text-slate-800">Generate GST Tax Invoice</h3>
          <p class="text-xs text-slate-500">Auto Intra/Inter-State Tax Split (CGST+SGST vs IGST) & Amount in Words</p>
        </div>
        <button onclick="closeNewInvoiceModal()" class="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-200">
          <i data-lucide="x" class="w-5 h-5"></i>
        </button>
      </div>

      <form id="newInvoiceForm" onsubmit="handleCreateInvoiceSubmit(event)" class="flex-1 overflow-y-auto p-6 space-y-5 custom-scrollbar">
        
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Invoice Type *</label>
            <select id="invType" onchange="toggleInvoiceType()" class="w-full text-xs p-2 rounded-lg border border-slate-200">
              <option value="B2B">B2B Tax Invoice</option>
              <option value="B2C">B2C Retail Invoice</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Invoice Number</label>
            <input type="text" id="invNumber" placeholder="Leave empty for auto" class="w-full text-xs p-2 rounded-lg border border-slate-200 font-mono" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Invoice Date *</label>
            <input type="date" id="invDate" required class="w-full text-xs p-2 rounded-lg border border-slate-200" />
          </div>
        </div>

        <div class="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-700 uppercase tracking-wider">Customer / Buyer Details</span>
            <select id="invCustomerSelect" onchange="handleCustomerSelect()" class="text-xs p-1.5 rounded-lg border border-slate-300 bg-white">
              <option value="">-- Choose Existing Customer --</option>
            </select>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label class="block text-[11px] font-semibold text-slate-600 mb-1">Customer Name *</label>
              <input type="text" id="invPartyName" required class="w-full text-xs p-2 rounded-lg border border-slate-200" />
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-slate-600 mb-1">Customer GSTIN</label>
              <input type="text" id="invPartyGstin" oninput="autoDetectBuyerStateFromGstin()" placeholder="e.g. 27AAGCA9988G1ZQ" class="w-full text-xs p-2 rounded-lg border border-slate-200 uppercase font-mono" />
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-slate-600 mb-1">Place of Supply (State) *</label>
              <select id="invPartyState" onchange="recalculateInvoiceLineItems()" class="w-full text-xs p-2 rounded-lg border border-slate-200"></select>
            </div>
            <div class="sm:col-span-3">
              <label class="block text-[11px] font-semibold text-slate-600 mb-1">Billing Address</label>
              <input type="text" id="invPartyAddress" placeholder="Street, City, Pincode" class="w-full text-xs p-2 rounded-lg border border-slate-200" />
            </div>
          </div>
        </div>

        <div>
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-bold text-slate-700 uppercase tracking-wider">Invoice Items</span>
            <button type="button" onclick="addInvoiceLineRow()" class="text-xs text-sky-600 hover:text-sky-700 font-semibold flex items-center gap-1">
              <i data-lucide="plus-circle" class="w-4 h-4"></i> Add Line Item
            </button>
          </div>

          <div class="border border-slate-200 rounded-xl overflow-hidden">
            <table class="w-full text-xs text-left">
              <thead class="bg-slate-100 text-slate-600 font-semibold border-b border-slate-200">
                <tr>
                  <th class="py-2.5 px-3">Item Description</th>
                  <th class="py-2.5 px-2 w-20">HSN/SAC</th>
                  <th class="py-2.5 px-2 w-16 text-center">Qty</th>
                  <th class="py-2.5 px-2 w-16 text-center">Unit</th>
                  <th class="py-2.5 px-2 w-24 text-right">Rate (₹)</th>
                  <th class="py-2.5 px-2 w-20 text-center">GST %</th>
                  <th class="py-2.5 px-3 w-28 text-right">Total (₹)</th>
                  <th class="py-2.5 px-2 w-10 text-center"></th>
                </tr>
              </thead>
              <tbody id="invoiceItemsTbody" class="divide-y divide-slate-100 font-medium"></tbody>
            </table>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4 rounded-xl bg-slate-900 text-white">
          <div class="text-xs space-y-1.5">
            <span class="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Tax Breakdown Mode:</span>
            <p id="invTaxTypeBadge" class="text-xs font-bold text-sky-400">Intra-State (CGST + SGST)</p>
            <p id="invWordsPreview" class="text-xs text-slate-300 italic mt-2">Zero Rupees Only</p>
          </div>

          <div class="text-xs space-y-1 text-right">
            <div class="flex justify-between text-slate-300"><span>Taxable Subtotal:</span><span id="invTaxableSubtotal" class="font-bold text-white">₹ 0.00</span></div>
            <div id="invCgstRow" class="flex justify-between text-slate-300"><span>CGST:</span><span id="invCgstTotal" class="font-bold text-white">₹ 0.00</span></div>
            <div id="invSgstRow" class="flex justify-between text-slate-300"><span>SGST:</span><span id="invSgstTotal" class="font-bold text-white">₹ 0.00</span></div>
            <div id="invIgstRow" class="flex justify-between text-slate-300 hidden"><span>IGST:</span><span id="invIgstTotal" class="font-bold text-white">₹ 0.00</span></div>
            <div class="pt-2 border-t border-slate-700 flex justify-between text-sm font-bold text-sky-400">
              <span>Total Invoice Amount:</span><span id="invGrandTotal">₹ 0.00</span>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Payment Status</label>
            <select id="invPaymentStatus" class="w-full text-xs p-2 rounded-lg border border-slate-200">
              <option value="UNPAID">Unpaid (Credit)</option>
              <option value="PAID">Fully Paid</option>
              <option value="PARTIAL">Partially Paid</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Amount Paid (₹)</label>
            <input type="number" id="invAmountPaid" step="any" value="0" class="w-full text-xs p-2 rounded-lg border border-slate-200" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Payment Mode</label>
            <select id="invPaymentMode" class="w-full text-xs p-2 rounded-lg border border-slate-200">
              <option value="UPI">UPI</option>
              <option value="NEFT">NEFT / Bank Transfer</option>
              <option value="CASH">Cash</option>
              <option value="CHEQUE">Cheque</option>
            </select>
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1">Invoice Notes</label>
          <input type="text" id="invNotes" placeholder="e.g. Delivered via Cargo, Po Reference" class="w-full text-xs p-2 rounded-lg border border-slate-200" />
        </div>

        <div class="pt-3 border-t border-slate-200 flex justify-end gap-3">
          <button type="button" onclick="closeNewInvoiceModal()" class="px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100">Cancel</button>
          <button type="submit" class="px-6 py-2 rounded-lg text-xs font-semibold text-white bg-sky-600 hover:bg-sky-700 shadow-sm transition">Save & Generate Invoice</button>
        </div>
      </form>
    </div>
  </div>

  <!-- ================= MODAL: UPLOAD PURCHASE BILL ================= -->
  <div id="uploadBillModal" class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm hidden z-50 flex items-center justify-center p-4 overflow-y-auto">
    <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-2xl max-h-[92vh] flex flex-col overflow-hidden">
      <div class="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/80 shrink-0">
        <div>
          <h3 class="text-base font-bold text-slate-800">Upload Purchase Bill & Claim Input Tax Credit (ITC)</h3>
          <p class="text-xs text-slate-500">Record vendor invoice with attached PDF/image and tag ITC eligibility</p>
        </div>
        <button onclick="closeUploadBillModal()" class="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-200"><i data-lucide="x" class="w-5 h-5"></i></button>
      </div>

      <form id="uploadBillForm" onsubmit="handleUploadBillSubmit(event)" class="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
        <div class="border-2 border-dashed border-slate-300 hover:border-emerald-500 rounded-xl p-4 text-center cursor-pointer transition bg-slate-50/50" onclick="document.getElementById('billFileInput').click()">
          <input type="file" id="billFileInput" accept="image/*,application/pdf" class="hidden" onchange="handleFileChosen(this)" />
          <i data-lucide="file-up" class="w-8 h-8 text-slate-400 mx-auto mb-1"></i>
          <p id="fileChosenLabel" class="text-xs font-semibold text-slate-700">Click to upload or drag & drop Supplier Bill (PDF / JPG / PNG)</p>
          <p class="text-[10px] text-slate-400 mt-0.5">Original bill file will be saved securely for GST audits</p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Supplier / Vendor Name *</label>
            <input type="text" id="billVendorName" required class="w-full text-xs p-2.5 rounded-lg border border-slate-200" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Supplier GSTIN (B2B)</label>
            <input type="text" id="billVendorGstin" placeholder="e.g. 24AAACD4433E1Z9" class="w-full text-xs p-2.5 rounded-lg border border-slate-200 uppercase font-mono" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Bill / Invoice Number *</label>
            <input type="text" id="billNumber" required class="w-full text-xs p-2.5 rounded-lg border border-slate-200 font-mono" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Bill Date *</label>
            <input type="date" id="billDate" required class="w-full text-xs p-2.5 rounded-lg border border-slate-200" />
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 rounded-xl bg-emerald-50/50 border border-emerald-200/80">
          <div>
            <label class="block text-xs font-semibold text-emerald-900 mb-1">Taxable Value (₹) *</label>
            <input type="number" id="billTaxable" step="any" required oninput="calcBillPreview()" class="w-full text-xs p-2.5 rounded-lg border border-emerald-200 bg-white font-bold" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-emerald-900 mb-1">GST Rate *</label>
            <select id="billGstRate" onchange="calcBillPreview()" class="w-full text-xs p-2.5 rounded-lg border border-emerald-200 bg-white">
              <option value="18">18% (Standard)</option>
              <option value="12">12%</option>
              <option value="5">5%</option>
              <option value="28">28%</option>
              <option value="0">0%</option>
            </select>
          </div>
          <div class="flex flex-col justify-center">
            <label class="text-xs font-semibold text-emerald-900 mb-1">Supply Type</label>
            <label class="inline-flex items-center gap-2 cursor-pointer mt-1">
              <input type="checkbox" id="billIsInterstate" onchange="calcBillPreview()" class="rounded text-emerald-600" />
              <span class="text-xs text-slate-700 font-medium">Inter-State (IGST)</span>
            </label>
          </div>
        </div>

        <div class="p-4 rounded-xl bg-slate-50 border border-slate-200">
          <label class="block text-xs font-bold text-slate-700 uppercase mb-2">Input Tax Credit (ITC) Eligibility *</label>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <label class="flex items-start gap-2.5 p-2.5 rounded-lg border border-slate-200 bg-white cursor-pointer hover:border-emerald-500">
              <input type="radio" name="itcEligibility" value="ELIGIBLE" checked class="mt-0.5 text-emerald-600" />
              <div>
                <span class="text-xs font-bold text-slate-800">🟢 Eligible ITC (Claim in GSTR-3B)</span>
                <p class="text-[10px] text-slate-500 mt-0.5">Purchases for business use eligible for credit</p>
              </div>
            </label>
            <label class="flex items-start gap-2.5 p-2.5 rounded-lg border border-slate-200 bg-white cursor-pointer hover:border-rose-500">
              <input type="radio" name="itcEligibility" value="INELIGIBLE_17_5" class="mt-0.5 text-rose-600" />
              <div>
                <span class="text-xs font-bold text-slate-800">🔴 Ineligible / Blocked Credit (Sec 17(5))</span>
                <p class="text-[10px] text-slate-500 mt-0.5">Food, catering, club, personal expenses</p>
              </div>
            </label>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Payment Status</label>
            <select id="billPaymentStatus" class="w-full text-xs p-2 rounded-lg border border-slate-200">
              <option value="PAID">Paid</option>
              <option value="UNPAID" selected>Unpaid / Credit</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Notes / Expense Category</label>
            <input type="text" id="billNotes" placeholder="e.g. Resale Goods, Office Supplies" class="w-full text-xs p-2 rounded-lg border border-slate-200" />
          </div>
        </div>

        <div class="pt-3 border-t border-slate-200 flex justify-end gap-3">
          <button type="button" onclick="closeUploadBillModal()" class="px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100">Cancel</button>
          <button type="submit" class="px-6 py-2 rounded-lg text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 shadow-sm transition">Save Bill & Record ITC</button>
        </div>
      </form>
    </div>
  </div>

  <!-- ================= MODAL: VIEW INVOICE (PRINTABLE) ================= -->
  <div id="viewInvoiceModal" class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm hidden z-50 flex items-center justify-center p-4 overflow-y-auto">
    <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-4xl max-h-[94vh] flex flex-col overflow-hidden">
      <div class="px-6 py-3 border-b border-slate-200 flex items-center justify-between bg-slate-50/80 shrink-0">
        <div class="flex items-center gap-3">
          <span class="text-xs font-bold px-2 py-0.5 rounded bg-sky-100 text-sky-700" id="viewInvTypeTag">TAX INVOICE</span>
          <h3 class="text-sm font-bold text-slate-800" id="viewInvNumberTitle">INV-001</h3>
        </div>
        <div class="flex items-center gap-2">
          <button onclick="printCurrentInvoice()" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold transition">
            <i data-lucide="printer" class="w-3.5 h-3.5"></i> Print
          </button>
          <a id="viewInvPdfDownloadBtn" href="#" target="_blank" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold transition">
            <i data-lucide="download" class="w-3.5 h-3.5"></i> Download PDF
          </a>
          <button onclick="closeViewInvoiceModal()" class="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-200 ml-2"><i data-lucide="x" class="w-5 h-5"></i></button>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-6 custom-scrollbar bg-slate-100 flex justify-center">
        <div id="printableInvoice" class="bg-white rounded-lg shadow-sm border border-slate-200 p-8 w-full max-w-3xl text-slate-900 text-xs"></div>
      </div>
    </div>
  </div>

  <!-- ================= MODAL: VIEW DOCUMENT ATTACHMENT ================= -->
  <div id="viewDocumentModal" class="fixed inset-0 bg-slate-900/70 backdrop-blur-sm hidden z-50 flex items-center justify-center p-4 overflow-y-auto">
    <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-4xl max-h-[92vh] flex flex-col overflow-hidden">
      <div class="px-6 py-3 border-b border-slate-200 flex items-center justify-between bg-slate-50 shrink-0">
        <h3 class="text-sm font-bold text-slate-800" id="docViewerTitle">Uploaded Purchase Invoice Document</h3>
        <button onclick="closeDocumentModal()" class="text-slate-400 hover:text-slate-600 p-1 rounded-lg"><i data-lucide="x" class="w-5 h-5"></i></button>
      </div>
      <div class="flex-1 p-4 bg-slate-900/10 flex items-center justify-center overflow-auto">
        <iframe id="docViewerFrame" class="w-full h-[70vh] border rounded-lg bg-white"></iframe>
      </div>
    </div>
  </div>

  <!-- ================= MODAL: ADD PARTY ================= -->
  <div id="newPartyModal" class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm hidden z-50 flex items-center justify-center p-4 overflow-y-auto">
    <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-lg p-6 space-y-4">
      <div class="flex justify-between items-center pb-2 border-b border-slate-200">
        <h3 class="text-base font-bold text-slate-800">Add Customer / Vendor</h3>
        <button onclick="closeNewPartyModal()"><i data-lucide="x" class="w-5 h-5 text-slate-400"></i></button>
      </div>
      <form id="newPartyForm" onsubmit="handleCreateParty(event)" class="space-y-3">
        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1">Party / Company Name *</label>
          <input type="text" id="partyNameInput" required class="w-full text-xs p-2.5 rounded-lg border border-slate-200" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Party Type</label>
            <select id="partyTypeInput" class="w-full text-xs p-2.5 rounded-lg border border-slate-200">
              <option value="CUSTOMER">Customer (Buyer)</option>
              <option value="VENDOR">Vendor (Supplier)</option>
              <option value="BOTH">Both</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">GSTIN</label>
            <input type="text" id="partyGstinInput" oninput="autoDetectPartyState()" placeholder="27XXXX..." class="w-full text-xs p-2.5 rounded-lg border border-slate-200 font-mono uppercase" />
          </div>
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1">State *</label>
          <select id="partyStateInput" class="w-full text-xs p-2.5 rounded-lg border border-slate-200"></select>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Phone</label>
            <input type="text" id="partyPhoneInput" class="w-full text-xs p-2.5 rounded-lg border border-slate-200" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Email</label>
            <input type="email" id="partyEmailInput" class="w-full text-xs p-2.5 rounded-lg border border-slate-200" />
          </div>
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1">Address</label>
          <input type="text" id="partyAddressInput" class="w-full text-xs p-2.5 rounded-lg border border-slate-200" />
        </div>
        <div class="pt-3 flex justify-end gap-2">
          <button type="button" onclick="closeNewPartyModal()" class="px-4 py-2 text-xs font-semibold text-slate-600">Cancel</button>
          <button type="submit" class="px-6 py-2 text-xs font-semibold text-white bg-sky-600 rounded-lg">Save Party</button>
        </div>
      </form>
    </div>
  </div>

  <!-- ================= MODAL: ADD ITEM ================= -->
  <div id="newItemModal" class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm hidden z-50 flex items-center justify-center p-4 overflow-y-auto">
    <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-md p-6 space-y-4">
      <div class="flex justify-between items-center pb-2 border-b border-slate-200">
        <h3 class="text-base font-bold text-slate-800">Add Product / Service Master</h3>
        <button onclick="closeNewItemModal()"><i data-lucide="x" class="w-5 h-5 text-slate-400"></i></button>
      </div>
      <form id="newItemForm" onsubmit="handleCreateItem(event)" class="space-y-3">
        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1">Item / Service Name *</label>
          <input type="text" id="itemNameInput" required class="w-full text-xs p-2.5 rounded-lg border border-slate-200" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">HSN / SAC Code</label>
            <input type="text" id="itemHsnInput" class="w-full text-xs p-2.5 rounded-lg border border-slate-200 font-mono" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Unit of Measurement (UOM)</label>
            <select id="itemUomInput" class="w-full text-xs p-2.5 rounded-lg border border-slate-200">
              <option value="Pcs">Pcs</option>
              <option value="Unit">Unit</option>
              <option value="Kg">Kg</option>
              <option value="Box">Box</option>
              <option value="Mtr">Mtr</option>
              <option value="Service">Service</option>
              <option value="Rim">Rim</option>
            </select>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Selling Price (₹) *</label>
            <input type="number" id="itemSellingPrice" step="any" required class="w-full text-xs p-2.5 rounded-lg border border-slate-200" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">GST Rate (%) *</label>
            <select id="itemGstRate" class="w-full text-xs p-2.5 rounded-lg border border-slate-200">
              <option value="18">18%</option>
              <option value="12">12%</option>
              <option value="5">5%</option>
              <option value="28">28%</option>
              <option value="0">0%</option>
            </select>
          </div>
        </div>
        <div class="pt-3 flex justify-end gap-2">
          <button type="button" onclick="closeNewItemModal()" class="px-4 py-2 text-xs font-semibold text-slate-600">Cancel</button>
          <button type="submit" class="px-6 py-2 text-xs font-semibold text-white bg-sky-600 rounded-lg">Save Product</button>
        </div>
      </form>
    </div>
  </div>

  <script src="/static/app.js"></script>
</body>
</html>
""")

with open(target_html, "a", encoding="utf-8") as f:
    f.write("".join(chunks))

print("index.html fully compiled successfully!")
