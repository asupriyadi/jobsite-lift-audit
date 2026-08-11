import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { downloadExcel } from "@/lib/api";
import { STATUSES, CHECKLIST_TYPES } from "@/lib/meta";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { MagnifyingGlass, ClipboardText, DownloadSimple } from "@phosphor-icons/react";

export default function InspectionList() {
  const navigate = useNavigate();
  const [rows, setRows] = useState([]);
  const [q, setQ] = useState("");
  const [type, setType] = useState("");
  const [status, setStatus] = useState("");
  const [site, setSite] = useState("");
  const [sites, setSites] = useState([]);

  useEffect(() => { api.get("/inspections/sites").then((r) => setSites(r.data)).catch(() => {}); }, []);

  const load = () => {
    const params = new URLSearchParams();
    if (q) params.append("q", q);
    if (type) params.append("checklist_type", type);
    if (status) params.append("status", status);
    if (site) params.append("site_name", site);
    api.get(`/inspections?${params}`).then((r) => setRows(r.data)).catch(() => {});
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [q, type, status, site]);

  return (
    <div className="space-y-5" data-testid="inspection-list">
      <div className="flex items-start justify-between">
        <div>
          <p className="overline text-accent">Historical Database</p>
          <h1 className="font-head text-2xl font-extrabold tracking-tight text-primary">Riwayat Laporan SIR</h1>
        </div>
        <Button variant="outline" onClick={downloadExcel} data-testid="export-excel"><DownloadSimple size={16} className="mr-1.5" /> Ekspor Excel</Button>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
        <div className="relative flex-1">
          <MagnifyingGlass size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} data-testid="search-input"
            placeholder="Cari job number, site, lift…" className="pl-9" />
        </div>
        <select value={site} onChange={(e) => setSite(e.target.value)} data-testid="filter-building"
          className="h-10 rounded-md border border-input bg-white px-3 text-sm">
          <option value="">Semua Gedung</option>
          {sites.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={type} onChange={(e) => setType(e.target.value)} data-testid="filter-type"
          className="h-10 rounded-md border border-input bg-white px-3 text-sm">
          <option value="">Semua Jenis</option>
          {CHECKLIST_TYPES.map((t) => <option key={t.key} value={t.key}>{t.key}</option>)}
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)} data-testid="filter-status"
          className="h-10 rounded-md border border-input bg-white px-3 text-sm">
          <option value="">Semua Status</option>
          {Object.entries(STATUSES).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
        </select>
      </div>

      {rows.length === 0 ? (
        <Card className="flex flex-col items-center gap-2 border-dashed py-16 text-muted-foreground">
          <ClipboardText size={32} />
          <p className="text-sm">Belum ada laporan.</p>
        </Card>
      ) : (
        <div className="grid gap-2.5 md:grid-cols-2">
          {rows.map((r) => (
            <button
              key={r.id}
              onClick={() => navigate(`/inspections/${r.id}`)}
              data-testid={`inspection-${r.id}`}
              className="rounded-lg border border-border bg-white p-4 text-left transition-colors hover:border-accent"
            >
              <div className="mb-2 flex items-start justify-between">
                <div className="min-w-0">
                  <p className="truncate font-head font-bold text-primary">{r.site_name}</p>
                  <p className="text-[11px] text-muted-foreground">{r.job_number} · Lift {r.lift_number}</p>
                </div>
                <span className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold ${STATUSES[r.status]?.color}`}>
                  {STATUSES[r.status]?.label}
                </span>
              </div>
              <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                <span className="rounded bg-secondary px-1.5 py-0.5 font-semibold text-primary">{r.checklist_type}</span>
                <span>{r.inspection_date}</span>
                <span>· {r.time_from}–{r.time_to}</span>
                <span className="ml-auto">{r.technician_name}</span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
