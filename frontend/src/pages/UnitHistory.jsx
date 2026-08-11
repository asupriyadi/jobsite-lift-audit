import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { STATUSES, judgmentByKey } from "@/lib/meta";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { MagnifyingGlass, ClipboardText, PhoneCall, HandArrowDown, Buildings } from "@phosphor-icons/react";

const KIND = {
  SIR: { icon: ClipboardText, color: "bg-blue-100 text-blue-700", path: (id) => `/inspections/${id}` },
  ECR: { icon: PhoneCall, color: "bg-amber-100 text-amber-700", path: (id) => `/reports/${id}` },
  HOR: { icon: HandArrowDown, color: "bg-emerald-100 text-emerald-700", path: (id) => `/reports/${id}` },
};

export default function UnitHistory() {
  const navigate = useNavigate();
  const [job, setJob] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const search = async (e) => {
    e?.preventDefault();
    if (!job.trim()) return;
    setLoading(true);
    try {
      const res = await api.get(`/units/history?job_number=${encodeURIComponent(job.trim())}`);
      setData(res.data);
    } catch (err) { setData({ events: [], building: {} }); }
    finally { setLoading(false); }
  };

  const b = data?.building || {};

  return (
    <div className="mx-auto max-w-3xl space-y-5" data-testid="unit-history">
      <div>
        <p className="overline text-accent">Riwayat per Unit</p>
        <h1 className="font-head text-2xl font-extrabold tracking-tight text-primary">Riwayat Pemeliharaan Unit</h1>
        <p className="text-sm text-muted-foreground">Masukkan Job Number untuk melihat gabungan SIR, ECR & HOR unit tersebut.</p>
      </div>

      <form onSubmit={search} className="flex gap-2">
        <div className="relative flex-1">
          <MagnifyingGlass size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <Input value={job} onChange={(e) => setJob(e.target.value)} data-testid="unit-job-input" placeholder="Job Number, mis. ZEZ3624" className="pl-9" />
        </div>
        <Button type="submit" disabled={loading} data-testid="unit-search" className="bg-primary">Cari</Button>
      </form>

      {data && (
        <>
          {b.job_number && (
            <Card className="border-border p-5" data-testid="unit-building">
              <div className="mb-2 flex items-center gap-2"><Buildings size={18} className="text-accent" /><h3 className="font-head font-bold text-primary">{b.site_name}</h3></div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-3">
                {[["Job Number", b.job_number], ["Kota", b.city], ["Supervisor", b.spv],
                  ["Kontrak", b.has_contract ? "Ya" : "Tidak"], ["Periode", b.maintenance_period],
                  ["Kontrak Berakhir", b.contract_end]].map(([l, v]) => (
                  <div key={l}><p className="overline text-muted-foreground">{l}</p><p className="text-sm font-semibold text-primary">{v || "-"}</p></div>
                ))}
              </div>
            </Card>
          )}

          <Card className="border-border p-5">
            <h3 className="font-head mb-3 font-bold text-primary">Timeline ({data.events.length})</h3>
            {data.events.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">Belum ada laporan untuk unit ini.</p>
            ) : (
              <div className="space-y-2">
                {data.events.map((ev) => {
                  const k = KIND[ev.kind] || KIND.SIR;
                  const Icon = k.icon;
                  return (
                    <button key={ev.id} onClick={() => navigate(k.path(ev.id))} data-testid={`unit-event-${ev.id}`}
                      className="flex w-full items-center gap-3 rounded-md border border-border bg-white p-3 text-left hover:border-accent">
                      <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md ${k.color}`}><Icon size={16} weight="bold" /></span>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-semibold text-primary">{ev.kind} · {ev.detail}</p>
                        <p className="text-[11px] text-muted-foreground">{ev.date} · {ev.technician}</p>
                      </div>
                      <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${STATUSES[ev.status]?.color}`}>{STATUSES[ev.status]?.label}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
