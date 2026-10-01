import os

target_html = r"C:\Users\One Click Solution\.gemini\antigravity\scratch\gst-invoicing-app\static\index.html"

with open(target_html, "r", encoding="utf-8") as f:
    content = f.read()

# Add Sales Person field into newInvoiceModal
old_header_grid = """        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
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
        </div>"""

new_header_grid = """        <div class="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Invoice Type *</label>
            <select id="invType" onchange="toggleInvoiceType()" class="w-full text-xs p-2 rounded-lg border border-slate-200">
              <option value="B2B">B2B Tax Invoice</option>
              <option value="B2C">B2C Retail Invoice</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Invoice Number</label>
            <input type="text" id="invNumber" placeholder="e.g. INVOICE/01" class="w-full text-xs p-2 rounded-lg border border-slate-200 font-mono" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Invoice Date *</label>
            <input type="date" id="invDate" required class="w-full text-xs p-2 rounded-lg border border-slate-200" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Sales Person</label>
            <input type="text" id="invSalesPerson" value="SUFIYAN SHAIKH" placeholder="e.g. SUFIYAN SHAIKH" class="w-full text-xs p-2 rounded-lg border border-slate-200 uppercase" />
          </div>
        </div>"""

content = content.replace(old_header_grid, new_header_grid)

with open(target_html, "w", encoding="utf-8") as f:
    f.write(content)

print("index.html updated with Sales Person field!")
