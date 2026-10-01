import os

target_html = r"C:\Users\One Click Solution\.gemini\antigravity\scratch\gst-invoicing-app\static\index.html"

chunks = []

chunks.append("""
      <!-- ================= TAB 2: SALES INVOICES ================= -->
      <section id="tab-sales" class="tab-view hidden space-y-6">
        <div class="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm">
          
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
            <div>
              <h3 class="text-lg font-bold text-slate-800">Sales Invoices (Outward Supplies)</h3>
              <p class="text-xs text-slate-500">Create, manage and print compliant B2B & B2C GST Tax Invoices</p>
            </div>
            <div class="flex flex-wrap items-center gap-3">
              <div class="relative">
                <i data-lucide="search" class="w-4 h-4 absolute left-3 top-2.5 text-slate-400"></i>
                <input type="text" id="salesSearchInput" oninput="filterSales()" placeholder="Search invoice, party, GSTIN..." class="text-xs pl-9 pr-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 w-60" />
              </div>

              <select id="salesTypeFilter" onchange="filterSales()" class="text-xs py-2 px-3 rounded-lg border border-slate-200 focus:outline-none">
                <option value="ALL">All Types</option>
                <option value="B2B">B2B (With GSTIN)</option>
                <option value="B2C">B2C (Retail)</option>
              </select>

              <select id="salesStatusFilter" onchange="filterSales()" class="text-xs py-2 px-3 rounded-lg border border-slate-200 focus:outline-none">
                <option value="ALL">All Status</option>
                <option value="PAID">Paid</option>
                <option value="PARTIAL">Partial</option>
                <option value="UNPAID">Unpaid</option>
              </select>

              <button onclick="openNewInvoiceModal()" class="flex items-center gap-2 bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition">
                <i data-lucide="plus" class="w-4 h-4"></i> Create Invoice
              </button>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs text-slate-600">
              <thead class="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
                <tr>
                  <th class="py-3 px-4">Invoice #</th>
                  <th class="py-3 px-4">Type</th>
                  <th class="py-3 px-4">Customer Name</th>
                  <th class="py-3 px-4">Customer GSTIN</th>
                  <th class="py-3 px-4">Date</th>
                  <th class="py-3 px-4 text-right">Taxable (₹)</th>
                  <th class="py-3 px-4 text-right">GST (₹)</th>
                  <th class="py-3 px-4 text-right">Total Value (₹)</th>
                  <th class="py-3 px-4 text-center">Status</th>
                  <th class="py-3 px-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody id="salesInvoicesTbody" class="divide-y divide-slate-100 font-medium"></tbody>
            </table>
          </div>

        </div>
      </section>

      <!-- ================= TAB 3: PURCHASE & BILL UPLOAD (ITC) ================= -->
      <section id="tab-purchases" class="tab-view hidden space-y-6">
        <div class="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm">
          
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
            <div>
              <div class="flex items-center gap-2">
                <h3 class="text-lg font-bold text-slate-800">Purchase Bills & ITC Upload Hub</h3>
                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-700 border border-emerald-200">Input Tax Credit Tracker</span>
              </div>
              <p class="text-xs text-slate-500">Upload physical / digital bills, track eligible ITC vs blocked 17(5) credits</p>
            </div>

            <div class="flex flex-wrap items-center gap-3">
              <div class="relative">
                <i data-lucide="search" class="w-4 h-4 absolute left-3 top-2.5 text-slate-400"></i>
                <input type="text" id="purchasesSearchInput" oninput="filterPurchases()" placeholder="Search bill, vendor, GSTIN..." class="text-xs pl-9 pr-3 py-2 rounded-lg border border-slate-200 focus:outline-none w-60" />
              </div>

              <select id="purchasesItcFilter" onchange="filterPurchases()" class="text-xs py-2 px-3 rounded-lg border border-slate-200 focus:outline-none">
                <option value="ALL">All ITC Types</option>
                <option value="ELIGIBLE">Eligible ITC</option>
                <option value="INELIGIBLE_17_5">Blocked / Ineligible 17(5)</option>
              </select>

              <button onclick="openUploadBillModal()" class="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition">
                <i data-lucide="upload-cloud" class="w-4 h-4"></i> Upload New Bill
              </button>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs text-slate-600">
              <thead class="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
                <tr>
                  <th class="py-3 px-4">Bill / Ref #</th>
                  <th class="py-3 px-4">Vendor Name</th>
                  <th class="py-3 px-4">Vendor GSTIN</th>
                  <th class="py-3 px-4">Bill Date</th>
                  <th class="py-3 px-4 text-right">Taxable (₹)</th>
                  <th class="py-3 px-4 text-right">Input GST (ITC)</th>
                  <th class="py-3 px-4 text-right">Total Amount (₹)</th>
                  <th class="py-3 px-4 text-center">ITC Eligibility</th>
                  <th class="py-3 px-4 text-center">Document</th>
                  <th class="py-3 px-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody id="purchaseBillsTbody" class="divide-y divide-slate-100 font-medium"></tbody>
            </table>
          </div>

        </div>
      </section>

      <!-- ================= TAB 4: GST CREDIT & TAX LEDGER ================= -->
      <section id="tab-itc-ledger" class="tab-view hidden space-y-6">
        <div class="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm">
          <div class="flex items-center justify-between pb-4 border-b border-slate-200">
            <div>
              <h3 class="text-lg font-bold text-slate-800">GST Input Tax Credit (ITC) Ledger & Set-off Reconciliation</h3>
              <p class="text-xs text-slate-500">Comprehensive view of Output Tax Liability vs Eligible Input Credit</p>
            </div>
            <a href="/api/reports/gstr3b/excel" target="_blank" class="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm transition">
              <i data-lucide="download" class="w-4 h-4"></i> Export GSTR-3B Excel
            </a>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
            <div class="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span class="text-xs font-bold text-slate-500 uppercase">Total Sales Tax</span>
              <p id="ledgerOutwardTotal" class="text-xl font-bold text-slate-800 mt-1">₹ 0.00</p>
              <div class="text-[11px] text-slate-500 mt-2 space-y-1">
                <div class="flex justify-between"><span>CGST:</span><span id="ledgerOutwardCgst" class="font-semibold">₹ 0.00</span></div>
                <div class="flex justify-between"><span>SGST:</span><span id="ledgerOutwardSgst" class="font-semibold">₹ 0.00</span></div>
                <div class="flex justify-between"><span>IGST:</span><span id="ledgerOutwardIgst" class="font-semibold">₹ 0.00</span></div>
              </div>
            </div>

            <div class="p-4 rounded-xl bg-emerald-50/60 border border-emerald-200">
              <span class="text-xs font-bold text-emerald-700 uppercase">Eligible Input ITC</span>
              <p id="ledgerItcTotal" class="text-xl font-bold text-emerald-700 mt-1">₹ 0.00</p>
              <div class="text-[11px] text-emerald-800 mt-2 space-y-1">
                <div class="flex justify-between"><span>CGST Credit:</span><span id="ledgerItcCgst" class="font-semibold">₹ 0.00</span></div>
                <div class="flex justify-between"><span>SGST Credit:</span><span id="ledgerItcSgst" class="font-semibold">₹ 0.00</span></div>
                <div class="flex justify-between"><span>IGST Credit:</span><span id="ledgerItcIgst" class="font-semibold">₹ 0.00</span></div>
              </div>
            </div>

            <div class="p-4 rounded-xl bg-rose-50/60 border border-rose-200">
              <span class="text-xs font-bold text-rose-700 uppercase">Blocked ITC (Sec 17(5))</span>
              <p id="ledgerBlockedItc" class="text-xl font-bold text-rose-700 mt-1">₹ 0.00</p>
              <p class="text-[11px] text-rose-600 mt-2">Ineligible for credit (food, personal, motor vehicles)</p>
            </div>

            <div class="p-4 rounded-xl bg-amber-50/80 border border-amber-200">
              <span class="text-xs font-bold text-amber-800 uppercase" id="ledgerNetStatusTitle">Net Tax to Pay</span>
              <p id="ledgerNetPayableTotal" class="text-xl font-bold text-amber-900 mt-1">₹ 0.00</p>
              <div class="text-[11px] text-amber-900 mt-2 space-y-1">
                <div class="flex justify-between"><span>Net CGST:</span><span id="ledgerNetCgst" class="font-semibold">₹ 0.00</span></div>
                <div class="flex justify-between"><span>Net SGST:</span><span id="ledgerNetSgst" class="font-semibold">₹ 0.00</span></div>
                <div class="flex justify-between"><span>Net IGST:</span><span id="ledgerNetIgst" class="font-semibold">₹ 0.00</span></div>
              </div>
            </div>
          </div>

          <div class="mt-6 p-4 rounded-xl bg-slate-900 text-slate-300 text-xs leading-relaxed">
            <h4 class="font-bold text-white mb-1 flex items-center gap-1.5">
              <i data-lucide="info" class="w-4 h-4 text-sky-400"></i> How GST Credit Set-Off Works (Govt Formula):
            </h4>
            <ul class="list-disc list-inside space-y-1 text-slate-400 mt-2">
              <li><b>IGST Credit</b> is utilized completely first against IGST liability, then CGST & SGST in any order.</li>
              <li><b>CGST Credit</b> is utilized against CGST liability, then IGST (Never against SGST).</li>
              <li><b>SGST Credit</b> is utilized against SGST liability, then IGST (Never against CGST).</li>
            </ul>
          </div>
        </div>
      </section>

      <!-- ================= TAB 5: PARTIES ================= -->
      <section id="tab-parties" class="tab-view hidden space-y-6">
        <div class="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
            <div>
              <h3 class="text-lg font-bold text-slate-800">Parties Master (Customers & Vendors)</h3>
              <p class="text-xs text-slate-500">Manage buyer and supplier records with GSTIN, State codes & addresses</p>
            </div>
            <button onclick="openNewPartyModal()" class="flex items-center gap-2 bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition">
              <i data-lucide="user-plus" class="w-4 h-4"></i> Add New Party
            </button>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs text-slate-600">
              <thead class="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
                <tr>
                  <th class="py-3 px-4">Party Name</th>
                  <th class="py-3 px-4">Category</th>
                  <th class="py-3 px-4">GSTIN</th>
                  <th class="py-3 px-4">State & Code</th>
                  <th class="py-3 px-4">Phone / Email</th>
                  <th class="py-3 px-4">Billing Address</th>
                  <th class="py-3 px-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody id="partiesTbody" class="divide-y divide-slate-100 font-medium"></tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- ================= TAB 6: INVENTORY ================= -->
      <section id="tab-inventory" class="tab-view hidden space-y-6">
        <div class="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
            <div>
              <h3 class="text-lg font-bold text-slate-800">Products & Services Master</h3>
              <p class="text-xs text-slate-500">HSN/SAC catalog, default GST rates, selling prices and unit master</p>
            </div>
            <button onclick="openNewItemModal()" class="flex items-center gap-2 bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition">
              <i data-lucide="plus" class="w-4 h-4"></i> Add Product / Service
            </button>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs text-slate-600">
              <thead class="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
                <tr>
                  <th class="py-3 px-4">Item Name</th>
                  <th class="py-3 px-4">HSN / SAC</th>
                  <th class="py-3 px-4">Unit (UOM)</th>
                  <th class="py-3 px-4 text-right">Selling Price (₹)</th>
                  <th class="py-3 px-4 text-right">Purchase Price (₹)</th>
                  <th class="py-3 px-4 text-center">GST Rate</th>
                  <th class="py-3 px-4 text-center">Stock Qty</th>
                  <th class="py-3 px-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody id="itemsTbody" class="divide-y divide-slate-100 font-medium"></tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- ================= TAB 7: GSTR REPORTS ================= -->
      <section id="tab-reports" class="tab-view hidden space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm flex flex-col justify-between">
            <div>
              <div class="flex items-center gap-3 mb-3">
                <div class="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center font-bold text-sm">G1</div>
                <div>
                  <h4 class="text-base font-bold text-slate-800">GSTR-1 Outward Sales Return</h4>
                  <p class="text-xs text-slate-500">Government compliant export format</p>
                </div>
              </div>
              <p class="text-xs text-slate-600 leading-relaxed mt-2">
                Includes B2B Invoices (Table 4), B2C Small Supplies (Table 7), and HSN-wise Sales Summary (Table 12) formatted for easy filing on the GST portal.
              </p>
            </div>
            <div class="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
              <span class="text-xs text-slate-400">Format: Microsoft Excel (.xlsx)</span>
              <a href="/api/reports/gstr1/excel" target="_blank" class="flex items-center gap-2 bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold px-4 py-2 rounded-lg transition">
                <i data-lucide="download" class="w-4 h-4"></i> Download GSTR-1
              </a>
            </div>
          </div>

          <div class="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm flex flex-col justify-between">
            <div>
              <div class="flex items-center gap-3 mb-3">
                <div class="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-sm">3B</div>
                <div>
                  <h4 class="text-base font-bold text-slate-800">GSTR-3B Monthly Return Summary</h4>
                  <p class="text-xs text-slate-500">Tax Liability vs Eligible ITC Summary</p>
                </div>
              </div>
              <p class="text-xs text-slate-600 leading-relaxed mt-2">
                Table 3.1 (Outward Taxable Supplies) and Table 4 (Eligible Input Tax Credit) with exact Net Tax Payable calculation for self-assessment.
              </p>
            </div>
            <div class="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
              <span class="text-xs text-slate-400">Format: Microsoft Excel (.xlsx)</span>
              <a href="/api/reports/gstr3b/excel" target="_blank" class="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold px-4 py-2 rounded-lg transition">
                <i data-lucide="download" class="w-4 h-4"></i> Download GSTR-3B
              </a>
            </div>
          </div>
        </div>
      </section>

      <!-- ================= TAB 8: SETTINGS ================= -->
      <section id="tab-settings" class="tab-view hidden space-y-6">
        <div class="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm max-w-4xl">
          <h3 class="text-lg font-bold text-slate-800 mb-1">Company Profile & GST Configuration</h3>
          <p class="text-xs text-slate-500 mb-6">These details will be printed on all your Tax Invoices and used for GST calculations.</p>

          <form id="companySettingsForm" onsubmit="saveCompanySettings(event)" class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Company / Trade Name *</label>
                <input type="text" id="cfgName" required class="w-full text-xs p-2.5 rounded-lg border border-slate-200" />
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Company GSTIN *</label>
                <input type="text" id="cfgGstin" oninput="autoDetectCompanyState()" required class="w-full text-xs p-2.5 rounded-lg border border-slate-200 uppercase font-mono" />
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">State *</label>
                <select id="cfgState" onchange="syncCompanyStateCode()" class="w-full text-xs p-2.5 rounded-lg border border-slate-200"></select>
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">State Code</label>
                <input type="text" id="cfgStateCode" readonly class="w-full text-xs p-2.5 rounded-lg bg-slate-50 border border-slate-200 font-mono" />
              </div>
              <div class="md:col-span-2">
                <label class="block text-xs font-semibold text-slate-700 mb-1">Registered Address</label>
                <input type="text" id="cfgAddress" class="w-full text-xs p-2.5 rounded-lg border border-slate-200" />
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">City</label>
                <input type="text" id="cfgCity" class="w-full text-xs p-2.5 rounded-lg border border-slate-200" />
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Pincode</label>
                <input type="text" id="cfgPincode" class="w-full text-xs p-2.5 rounded-lg border border-slate-200" />
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Phone Number</label>
                <input type="text" id="cfgPhone" class="w-full text-xs p-2.5 rounded-lg border border-slate-200" />
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
                <input type="email" id="cfgEmail" class="w-full text-xs p-2.5 rounded-lg border border-slate-200" />
              </div>
            </div>

            <div class="pt-4 border-t border-slate-200">
              <h4 class="text-sm font-bold text-slate-800 mb-3">Bank & UPI Payment Details (For Invoice Printing)</h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="block text-xs font-semibold text-slate-700 mb-1">Bank Name</label>
                  <input type="text" id="cfgBankName" class="w-full text-xs p-2.5 rounded-lg border border-slate-200" />
                </div>
                <div>
                  <label class="block text-xs font-semibold text-slate-700 mb-1">Account Number</label>
                  <input type="text" id="cfgBankAcc" class="w-full text-xs p-2.5 rounded-lg border border-slate-200 font-mono" />
                </div>
                <div>
                  <label class="block text-xs font-semibold text-slate-700 mb-1">IFSC Code</label>
                  <input type="text" id="cfgBankIfsc" class="w-full text-xs p-2.5 rounded-lg border border-slate-200 uppercase font-mono" />
                </div>
                <div>
                  <label class="block text-xs font-semibold text-slate-700 mb-1">UPI ID</label>
                  <input type="text" id="cfgUpiId" class="w-full text-xs p-2.5 rounded-lg border border-slate-200 font-mono" />
                </div>
              </div>
            </div>

            <div class="pt-4 border-t border-slate-200">
              <h4 class="text-sm font-bold text-slate-800 mb-3">Invoice Numbering & Terms</h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="block text-xs font-semibold text-slate-700 mb-1">Invoice Prefix</label>
                  <input type="text" id="cfgPrefix" class="w-full text-xs p-2.5 rounded-lg border border-slate-200" />
                </div>
                <div class="md:col-span-2">
                  <label class="block text-xs font-semibold text-slate-700 mb-1">Terms & Conditions</label>
                  <textarea id="cfgTerms" rows="3" class="w-full text-xs p-2.5 rounded-lg border border-slate-200"></textarea>
                </div>
              </div>
            </div>

            <div class="pt-4 flex justify-end">
              <button type="submit" class="flex items-center gap-2 bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold px-6 py-2.5 rounded-lg shadow-sm transition">
                <i data-lucide="check" class="w-4 h-4"></i> Save Company Profile
              </button>
            </div>
          </form>
        </div>
      </section>

    </div>
  </main>
""")

with open(target_html, "a", encoding="utf-8") as f:
    f.write("".join(chunks))

print("Part 3 written successfully")
