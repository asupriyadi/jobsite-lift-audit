import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { STATUSES, ROLE_LABELS } from "@/lib/meta";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  ClipboardText, Wrench, CheckCircle, Clock, Plus, ArrowRight,
} from "@phosphor-icons/react";
import {
  BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, Tooltip,
} from "recharts";

const INV_COLORS = {
  pending: "#94A3B8", available: "#10B981", ordering: "#3B82F6",
  no_stock: "#EF4444", discontinued: "#A855F7",
};
const INV_LABEL = {
  pending: "Pending", available: "Tersedia", ordering: "Dipesan",
  no_stock: "No Stok", discontinued: "Discontinue",
};

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);

  useEffect(() => {
    api.get("/dashboard/stats").then((r) => setStats(r.data)).catch(() => {});
  }, []);

  if (!stats) return <div className="text-sm text-muted-foreground">Memuat dashboard…</div>;

  const cards = [
    { label: "Total Inspeksi", value: stats.total_inspections, icon: ClipboardText, color: "text-blue-600 bg-blue-50" },
    { label: "Menunggu Approve", value: (stats.by_status.submitted || 0) + (stats.by_status.checked || 0), icon: Clock, color: "text-amber-600 bg-amber-50" },
    { label: "Approved", value: stats.by_status.approved || 0, icon: CheckCircle, color: "text-emerald-600 bg-emerald-50" },
    { label: "Spare Part Open", value: stats.spare_open, icon: Wrench, color: "text-red-600 bg-red-50" },
  ];

  const invData = Object.entries(stats.inventory_breakdown)
    .map(([k, v]) => ({ name: INV_LABEL[k], key: k, value: v }))
    .filter((d) => d.value > 0);

  return (
    <div className="space-y-6" data-testid="dashboard">
      <div className="flex items-end justify-between">
        <div>
          <p className="overline text-accent">Dashboard · {ROLE_LABELS[user.role]}</p>
          <h1 className="font-head text-2xl font-extrabold tracking-tight text-primary md:text-3xl">
            Halo, {user.name.split(" ")[0]} 👋
          </h1>
        </div>
        {["technician", "supervisor", "head_maintenance", "admin"].includes(user.role) && (
          <Button onClick={() => navigate("/inspections/new")} data-testid="dash-new-inspection"
            className="bg-accent hover:bg-accent/90">
            <Plus size={16} className="mr-1" /> Inspeksi Baru
          </Button>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {cards.map((c) => (
          <Card key={c.label} className="border-border p-4">
            <div className={`mb-3 flex h-9 w-9 items-center justify-center rounded-md ${c.color}`}>
              <c.icon size={18} weight="bold" />
            </div>
            <p className="font-head text-2xl font-extrabold text-primary">{c.value}</p>
            <p className="text-xs text-muted-foreground">{c.label}</p>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="border-border p-5 lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-head font-bold text-primary">Inspeksi Terbaru</h3>
            <button onClick={() => navigate("/inspections")} className="text-xs font-semibold text-accent">
              Lihat semua
            </button>
          </div>
          <div className="space-y-2">
            {stats.recent.length === 0 && (
              <p className="py-8 text-center text-sm text-muted-foreground">Belum ada data inspeksi.</p>
            )}
            {stats.recent.map((r) => (
              <button
                key={r.id}
                onClick={() => navigate(`/inspections/${r.id}`)}
                data-testid={`recent-${r.id}`}
                className="flex w-full items-center justify-between rounded-md border border-border bg-white px-3 py-2.5 text-left hover:border-accent transition-colors"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-primary">
                    {r.site_name} · {r.lift_number}
                  </p>
                  <p className="text-[11px] text-muted-foreground">
                    {r.job_number} · {r.checklist_type} · {r.inspection_date}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${STATUSES[r.status]?.color}`}>
                    {STATUSES[r.status]?.label}
                  </span>
                  <ArrowRight size={14} className="text-slate-400" />
                </div>
              </button>
            ))}
          </div>
        </Card>

        <Card className="border-border p-5">
          <h3 className="font-head mb-1 font-bold text-primary">Ketersediaan Spare Part</h3>
          <p className="mb-3 text-xs text-muted-foreground">Status inventory ({stats.spare_total} item)</p>
          {invData.length === 0 ? (
            <p className="py-10 text-center text-sm text-muted-foreground">Belum ada permintaan spare part.</p>
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={invData} layout="vertical" margin={{ left: 0, right: 10 }}>
                <XAxis type="number" hide />
                <YAxis type="category" dataKey="name" width={70} tick={{ fontSize: 11 }} />
                <Tooltip cursor={{ fill: "#f1f5f9" }} />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {invData.map((d) => <Cell key={d.key} fill={INV_COLORS[d.key]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
          <Button variant="outline" onClick={() => navigate("/spare-parts")}
            data-testid="dash-spareparts" className="mt-3 w-full">
            Kelola Spare Part
          </Button>
        </Card>
      </div>
    </div>
  );
}
