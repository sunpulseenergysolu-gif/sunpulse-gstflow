import os

target_html = r"C:\Users\One Click Solution\.gemini\antigravity\scratch\gst-invoicing-app\static\index.html"

chunks = []

chunks.append("""
  <!-- Main Content Body -->
  <main class="flex-1 flex flex-col min-w-0 overflow-hidden">
    
    <!-- Top Header Bar -->
    <header class="h-16 bg-white border-b border-slate-200/80 px-6 flex items-center justify-between shrink-0 shadow-sm">
      <div class="flex items-center gap-4">
        <h2 id="topHeaderTitle" class="text-lg font-bold text-slate-800">GST Overview & ITC Dashboard</h2>
      </div>

      <div class="flex items-center gap-3">
        <button onclick="openNewInvoiceModal()" class="flex items-center gap-2 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white text-xs font-semibold px-3.5 py-2 rounded-lg shadow-sm shadow-sky-600/20 transition">
          <i data-lucide="plus" class="w-4 h-4"></i> New Tax Invoice
        </button>

        <button onclick="openUploadBillModal()" class="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-3.5 py-2 rounded-lg shadow-sm shadow-emerald-600/20 transition">
          <i data-lucide="upload" class="w-4 h-4"></i> Upload Purchase Bill
        </button>

        <button onclick="loadDashboardData()" title="Refresh Data" class="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition border border-slate-200">
          <i data-lucide="refresh-cw" class="w-4 h-4"></i>
        </button>
      </div>
    </header>

    <!-- Dynamic Tab Content Wrapper -->
    <div class="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar bg-slate-50/50">

      <!-- ================= TAB 1: DASHBOARD & ITC ================= -->
      <section id="tab-dashboard" class="tab-view space-y-6">
        
        <!-- Key Metrics Cards Row -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          
          <div class="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-sm relative overflow-hidden group hover:border-indigo-300 transition">
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold uppercase tracking-wider text-slate-500">Output Tax Liability</span>
              <div class="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
                <i data-lucide="arrow-up-right" class="w-4 h-4"></i>
              </div>
            </div>
            <p id="cardOutputTax" class="text-2xl font-extrabold text-slate-800 mt-3">₹ 0.00</p>
            <div class="flex items-center gap-2 mt-2 text-xs text-slate-500">
              <span class="text-indigo-600 font-semibold" id="cardSalesCount">0 Invoices</span>
              <span>• Total Sales Tax</span>
            </div>
            <div class="absolute bottom-0 left-0 right-0 h-1 bg-indigo-500"></div>
          </div>

          <div class="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-sm relative overflow-hidden group hover:border-emerald-300 transition">
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold uppercase tracking-wider text-slate-500">Input Tax Credit (ITC)</span>
              <div class="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <i data-lucide="arrow-down-left" class="w-4 h-4"></i>
              </div>
            </div>
            <p id="cardInputTax" class="text-2xl font-extrabold text-emerald-600 mt-3">₹ 0.00</p>
            <div class="flex items-center gap-2 mt-2 text-xs text-slate-500">
              <span class="text-emerald-600 font-semibold" id="cardPurchaseCount">0 Bills</span>
              <span>• Available for Offset</span>
            </div>
            <div class="absolute bottom-0 left-0 right-0 h-1 bg-emerald-500"></div>
          </div>

          <div class="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-sm relative overflow-hidden group hover:border-amber-300 transition">
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold uppercase tracking-wider text-slate-500" id="cardNetLabel">Net GST Payable</span>
              <div class="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
                <i data-lucide="scale" class="w-4 h-4"></i>
              </div>
            </div>
            <p id="cardNetPayable" class="text-2xl font-extrabold text-slate-800 mt-3">₹ 0.00</p>
            <div class="flex items-center gap-2 mt-2 text-xs text-slate-500">
              <span id="cardNetSubtext" class="text-amber-600 font-semibold">After ITC Offset</span>
            </div>
            <div id="cardNetBar" class="absolute bottom-0 left-0 right-0 h-1 bg-amber-500"></div>
          </div>

          <div class="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-sm relative overflow-hidden group hover:border-sky-300 transition">
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Sales Turnover</span>
              <div class="w-8 h-8 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center">
                <i data-lucide="trending-up" class="w-4 h-4"></i>
              </div>
            </div>
            <p id="cardTotalSales" class="text-2xl font-extrabold text-slate-800 mt-3">₹ 0.00</p>
            <div class="flex items-center gap-2 mt-2 text-xs text-slate-500">
              <span class="text-rose-500 font-medium" id="cardReceivables">₹0 Due</span>
              <span>• Pending Receivables</span>
            </div>
            <div class="absolute bottom-0 left-0 right-0 h-1 bg-sky-500"></div>
          </div>

        </div>

        <!-- ITC Pool Breakdown -->
        <div class="bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 rounded-2xl p-6 text-white shadow-xl">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
            <div>
              <div class="flex items-center gap-2">
                <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-sky-500/20 text-sky-400 border border-sky-500/30 uppercase tracking-wider">
                  Live ITC Pool
                </span>
                <h3 class="text-lg font-bold text-white">GST Input Tax Credit Ledger & Set-Off Status</h3>
              </div>
              <p class="text-xs text-slate-400 mt-1">Automatic CGST, SGST & IGST tax credit adjustment compliant with GST rules.</p>
            </div>
            <div class="flex items-center gap-2">
              <button onclick="switchTab('itc-ledger')" class="px-3.5 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-xs font-semibold text-white transition flex items-center gap-1.5 border border-white/10">
                <i data-lucide="file-text" class="w-3.5 h-3.5"></i> Detailed ITC Ledger
              </button>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            
            <div class="bg-slate-800/70 rounded-xl p-4 border border-slate-700/60 backdrop-blur">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-bold text-sky-300">Central Tax (CGST)</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-300">50% Intra-State</span>
              </div>
              <div class="space-y-2 text-xs">
                <div class="flex justify-between text-slate-300"><span>Output Liability:</span><span id="poolCgstOutput" class="font-bold text-white">₹ 0.00</span></div>
                <div class="flex justify-between text-slate-300"><span>Input Credit (ITC):</span><span id="poolCgstInput" class="font-bold text-emerald-400">₹ 0.00</span></div>
                <div class="pt-2 border-t border-slate-700/80 flex justify-between font-semibold">
                  <span class="text-slate-400">Net CGST Payable:</span><span id="poolCgstNet" class="text-amber-300 font-bold">₹ 0.00</span>
                </div>
              </div>
            </div>

            <div class="bg-slate-800/70 rounded-xl p-4 border border-slate-700/60 backdrop-blur">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-bold text-indigo-300">State Tax (SGST)</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300">50% Intra-State</span>
              </div>
              <div class="space-y-2 text-xs">
                <div class="flex justify-between text-slate-300"><span>Output Liability:</span><span id="poolSgstOutput" class="font-bold text-white">₹ 0.00</span></div>
                <div class="flex justify-between text-slate-300"><span>Input Credit (ITC):</span><span id="poolSgstInput" class="font-bold text-emerald-400">₹ 0.00</span></div>
                <div class="pt-2 border-t border-slate-700/80 flex justify-between font-semibold">
                  <span class="text-slate-400">Net SGST Payable:</span><span id="poolSgstNet" class="text-amber-300 font-bold">₹ 0.00</span>
                </div>
              </div>
            </div>

            <div class="bg-slate-800/70 rounded-xl p-4 border border-slate-700/60 backdrop-blur">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-bold text-purple-300">Integrated Tax (IGST)</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300">Inter-State</span>
              </div>
              <div class="space-y-2 text-xs">
                <div class="flex justify-between text-slate-300"><span>Output Liability:</span><span id="poolIgstOutput" class="font-bold text-white">₹ 0.00</span></div>
                <div class="flex justify-between text-slate-300"><span>Input Credit (ITC):</span><span id="poolIgstInput" class="font-bold text-emerald-400">₹ 0.00</span></div>
                <div class="pt-2 border-t border-slate-700/80 flex justify-between font-semibold">
                  <span class="text-slate-400">Net IGST Payable:</span><span id="poolIgstNet" class="text-amber-300 font-bold">₹ 0.00</span>
                </div>
              </div>
            </div>

          </div>
        </div>

        <!-- Recent Activity Table -->
        <div class="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-base font-bold text-slate-800">Recent Sales & Purchase Activity</h3>
              <p class="text-xs text-slate-500">Latest outward tax invoices and inward vendor purchase bills</p>
            </div>
            <button onclick="switchTab('sales')" class="text-xs font-semibold text-sky-600 hover:text-sky-700 flex items-center gap-1">
              View All Sales <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
            </button>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs text-slate-600">
              <thead class="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
                <tr>
                  <th class="py-3 px-4">Type</th>
                  <th class="py-3 px-4">Ref / Invoice No</th>
                  <th class="py-3 px-4">Party Name</th>
                  <th class="py-3 px-4">Date</th>
                  <th class="py-3 px-4 text-right">Tax (₹)</th>
                  <th class="py-3 px-4 text-right">Total (₹)</th>
                  <th class="py-3 px-4 text-center">Status</th>
                  <th class="py-3 px-4 text-center">Category</th>
                </tr>
              </thead>
              <tbody id="recentActivityTbody" class="divide-y divide-slate-100 font-medium">
              </tbody>
            </table>
          </div>
        </div>

      </section>
""")

with open(target_html, "a", encoding="utf-8") as f:
    f.write("".join(chunks))

print("Part 2 written successfully")
