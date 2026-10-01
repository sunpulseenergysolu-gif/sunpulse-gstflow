import os

target_html = r"C:\Users\One Click Solution\.gemini\antigravity\scratch\gst-invoicing-app\static\index.html"

chunks = []

chunks.append("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>GSTFlow - Smart GST Invoicing & ITC Credit Management</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: { 50: '#f0f7ff', 100: '#e0effe', 500: '#0284c7', 600: '#0369a1', 700: '#075985', 800: '#0c4a6e', 900: '#1e3a8a' }
          }
        }
      }
    }
  </script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    body { font-family: 'Plus Jakarta Sans', sans-serif; }
    .custom-scrollbar::-webkit-scrollbar { width: 6px; height: 6px; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background-color: #cbd5e1; border-radius: 4px; }
    @media print {
      body * { visibility: hidden; }
      #printableInvoice, #printableInvoice * { visibility: visible; }
      #printableInvoice { position: absolute; left: 0; top: 0; width: 100%; margin: 0; padding: 15px; background: white; }
    }
  </style>
</head>
<body class="bg-slate-50 text-slate-900 min-h-screen flex antialiased">
""")

chunks.append("""
  <!-- Sidebar -->
  <aside class="w-64 bg-slate-900 text-slate-300 flex flex-col shrink-0 border-r border-slate-800 select-none">
    <div class="h-16 flex items-center gap-3 px-6 border-b border-slate-800 bg-slate-950/40">
      <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-sky-500/20 font-bold text-lg">G</div>
      <div>
        <h1 class="text-base font-bold text-white tracking-tight flex items-center gap-1.5">GSTFlow <span class="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-400 border border-sky-500/30">Pro</span></h1>
        <p class="text-[11px] text-slate-400">Invoicing & ITC Engine</p>
      </div>
    </div>

    <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto custom-scrollbar">
      <button onclick="switchTab('dashboard')" id="nav-dashboard" class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all bg-sky-600/20 text-sky-400 border border-sky-500/30"><i data-lucide="layout-dashboard" class="w-4 h-4"></i> Dashboard & ITC</button>
      <button onclick="switchTab('sales')" id="nav-sales" class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all text-slate-400 hover:text-white hover:bg-slate-800/60"><i data-lucide="receipt" class="w-4 h-4"></i> Sales Invoices</button>
      <button onclick="switchTab('purchases')" id="nav-purchases" class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all text-slate-400 hover:text-white hover:bg-slate-800/60"><i data-lucide="file-up" class="w-4 h-4"></i> Purchase & Bills <span class="ml-auto text-[10px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-semibold px-1.5 py-0.5 rounded">ITC</span></button>
      <button onclick="switchTab('itc-ledger')" id="nav-itc-ledger" class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all text-slate-400 hover:text-white hover:bg-slate-800/60"><i data-lucide="scale" class="w-4 h-4"></i> GST Credit Ledger</button>
      <button onclick="switchTab('parties')" id="nav-parties" class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all text-slate-400 hover:text-white hover:bg-slate-800/60"><i data-lucide="users" class="w-4 h-4"></i> Parties Master</button>
      <button onclick="switchTab('inventory')" id="nav-inventory" class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all text-slate-400 hover:text-white hover:bg-slate-800/60"><i data-lucide="package" class="w-4 h-4"></i> Products & HSN</button>
      <button onclick="switchTab('reports')" id="nav-reports" class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all text-slate-400 hover:text-white hover:bg-slate-800/60"><i data-lucide="file-spreadsheet" class="w-4 h-4"></i> GSTR-1 & 3B Reports</button>
      <button onclick="switchTab('settings')" id="nav-settings" class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all text-slate-400 hover:text-white hover:bg-slate-800/60"><i data-lucide="settings" class="w-4 h-4"></i> Company Profile</button>
    </nav>

    <div class="p-3 m-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
      <div class="flex items-center gap-2 mb-1.5">
        <div class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
        <span class="text-[11px] font-semibold text-slate-300 uppercase tracking-wider">Active GST Profile</span>
      </div>
      <p id="sidebarCompanyName" class="text-xs font-bold text-white truncate">Bharat Tech Solutions</p>
      <p id="sidebarGstin" class="text-[10px] text-sky-400 font-mono mt-0.5">27AABCB1234F1Z5</p>
    </div>
  </aside>
""")

with open(target_html, "w", encoding="utf-8") as f:
    f.write("".join(chunks))

print("Part 1 written successfully")
