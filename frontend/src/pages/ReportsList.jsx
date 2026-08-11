import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { downloadExcel } from "@/lib/api";
import { STATUSES } from "@/lib/meta";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { MagnifyingGlass, PhoneCall, HandArrowDown, FileText, DownloadSimple } from "@phosphor-icons/react";

const TYPE_META = {
  ECR: { label: "ECR · Call Back", icon: PhoneCall, color: "bg-amber-100 text-amber-700" },
  HOR: { label: "HOR · Hand Over", icon: HandArrowDown, color: "bg-emerald-100 text-emerald-700" },
};

export default function ReportsList() {
  const navigate = useNavigate();
  const [rows, setRows] = useState([]);
  const [q, setQ] = useState("");
  const [type, setType] = useState("");

  useEffect(() => {
    const p = new URLSearchParams();
    if (q) p.append("q", q);
    if (type) p.append("type", type);
    api.get(`/reports?${p}`).then((r) => setRows(r.data)).catch(() => {});
  }, [q, type]);

  return (
    <div className="space-y-5" data-testid="reports-list">
      <div className="flex items-start justify-between">
        <div>
          <p className="overline text-accent">Historical Database</p>
          <h1 className="font-head text-2xl font-extrabold tracking-tight text-primary">Laporan ECR & HOR</h1>
        </div>
        <Button variant="outline" onClick={downloadExcel} data-testid="reports-export-excel"><DownloadSimple size={16} className="mr-1.5" /> Ekspor Excel</Button>
      </div>
      <div className="flex flex-col gap-2 sm:flex-row">
        <div className="relative flex-1">
          <MagnifyingGlass size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} data-testid="reports-search" placeholder="Cari site, job number, unit…" className="pl-9" />
        </div>
        <select value={type} onChange={(e) => setType(e.target.value)} data-testid="reports-filter-type" className="h-10 rounded-md border border-input bg-white px-3 text-sm">
          <option value="">Semua Jenis</option>
          <option value="ECR">ECR</option>
          <option value="HOR">HOR</option>
        </select>
      </div>

      {rows.length === 0 ? (
        <Card className="flex flex-col items-center gap-2 border-dashed py-16 text-muted-foreground">
          <FileText size={32} /><p className="text-sm">Belum ada laporan ECR / HOR.</p>
        </Card>
      ) : (
        <div className="grid gap-2.5 md:grid-cols-2">
          {rows.map((r) => {
            const m = TYPE_META[r.report_type] || {};
            const Icon = m.icon || FileText;
            return (
              <button key={r.id} onClick={() => navigate(`/reports/${r.id}`)} data-testid={`report-${r.id}`}
                className="rounded-lg border border-border bg-white p-4 text-left transition-colors hover:border-accent">
                <div className="mb-2 flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`flex h-8 w-8 items-center justify-center rounded-md ${m.color}`}><Icon size={16} weight="bold" /></span>
                    <div>
                      <p className="font-head font-bold text-primary">{r.site_name || "-"}</p>
                      <p className="text-[11px] text-muted-foreground">{r.job_number || ""} · {r.unit_no || r.lift_number || ""}</p>
                    </div>
                  </div>
                  <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${STATUSES[r.status]?.color}`}>{STATUSES[r.status]?.label}</span>
                </div>
                <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                  <span className="rounded bg-secondary px-1.5 py-0.5 font-semibold text-primary">{r.report_type}</span>
                  <span>{r.report_date}</span>
                  <span className="ml-auto">{r.technician_name}</span>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
