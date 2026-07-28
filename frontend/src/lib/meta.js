export const JUDGMENTS = [
  { key: "good", mark: "✔", label: "Good", color: "#10B981", bg: "bg-emerald-500", text: "text-emerald-600", ring: "ring-emerald-500", soft: "bg-emerald-50 border-emerald-200" },
  { key: "replaced", mark: "◎", label: "Replaced/Adjusted", color: "#F59E0B", bg: "bg-amber-500", text: "text-amber-600", ring: "ring-amber-500", soft: "bg-amber-50 border-amber-200" },
  { key: "damage", mark: "✖", label: "Damage", color: "#EF4444", bg: "bg-red-500", text: "text-red-600", ring: "ring-red-500", soft: "bg-red-50 border-red-200" },
  { key: "none", mark: "▬", label: "None", color: "#94A3B8", bg: "bg-slate-400", text: "text-slate-500", ring: "ring-slate-400", soft: "bg-slate-50 border-slate-200" },
];
export const judgmentByKey = (k) => JUDGMENTS.find((j) => j.key === k);

export const CHECKLIST_TYPES = [
  { key: "1M", label: "1M — Checklist Bulanan", desc: "Setiap bulan" },
  { key: "3M", label: "3M — Checklist 3 Bulanan", desc: "Jan, Apr, Jul, Okt" },
  { key: "12M", label: "12M — Checklist 12 Bulanan", desc: "Desember" },
];

export const STATUSES = {
  draft: { label: "Draft", color: "bg-slate-100 text-slate-700 border-slate-200" },
  submitted: { label: "Submitted", color: "bg-blue-100 text-blue-700 border-blue-200" },
  checked: { label: "Checked", color: "bg-amber-100 text-amber-700 border-amber-200" },
  approved: { label: "Approved", color: "bg-emerald-100 text-emerald-700 border-emerald-200" },
};

export const ROLE_LABELS = {
  admin: "Administrator",
  technician: "Teknisi",
  supervisor: "Supervisor",
  head_maintenance: "Kepala Maintenance",
  sales: "Sales / Penawaran",
  inventory: "Inventory",
  customer: "Customer",
};

export const SPARE_FIELDS = {
  sales_status: {
    label: "Sales / Penawaran",
    roles: ["sales", "supervisor", "head_maintenance", "admin"],
    options: [
      { v: "pending", l: "Pending", c: "bg-slate-100 text-slate-600" },
      { v: "offered", l: "Sudah Ditawarkan", c: "bg-emerald-100 text-emerald-700" },
    ],
  },
  customer_po_status: {
    label: "Customer (PO)",
    roles: ["customer", "sales", "supervisor", "head_maintenance", "admin"],
    options: [
      { v: "pending", l: "Belum PO", c: "bg-slate-100 text-slate-600" },
      { v: "po_issued", l: "PO Terbit", c: "bg-emerald-100 text-emerald-700" },
    ],
  },
  inventory_status: {
    label: "Inventory",
    roles: ["inventory", "supervisor", "head_maintenance", "admin"],
    options: [
      { v: "pending", l: "Pending", c: "bg-slate-100 text-slate-600" },
      { v: "available", l: "Tersedia", c: "bg-emerald-100 text-emerald-700" },
      { v: "ordering", l: "Sedang Dipesan", c: "bg-blue-100 text-blue-700" },
      { v: "no_stock", l: "Tidak Ada Stok", c: "bg-red-100 text-red-700" },
      { v: "discontinued", l: "Discontinue", c: "bg-purple-100 text-purple-700" },
    ],
  },
  maintenance_status: {
    label: "Maintenance",
    roles: ["technician", "supervisor", "head_maintenance", "admin"],
    options: [
      { v: "pending", l: "Belum Diganti", c: "bg-slate-100 text-slate-600" },
      { v: "replaced", l: "Sudah Diganti", c: "bg-emerald-100 text-emerald-700" },
    ],
  },
};

export const spareOptionMeta = (field, value) =>
  SPARE_FIELDS[field]?.options.find((o) => o.v === value);
