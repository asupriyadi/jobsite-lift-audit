import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { SPARE_FIELDS, spareOptionMeta } from "@/lib/meta";
import { Card } from "@/components/ui/card";
import {
  Table, TableHeader, TableBody, TableRow, TableHead, TableCell,
} from "@/components/ui/table";
import { Wrench } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function SpareParts() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [rows, setRows] = useState([]);
  const [invFilter, setInvFilter] = useState("");
  const [onlyOpen, setOnlyOpen] = useState(false);

  const load = () => {
    const params = new URLSearchParams();
    if (invFilter) params.append("inventory_status", invFilter);
    if (onlyOpen) params.append("only_open", "true");
    api.get(`/spare-parts?${params}`).then((r) => setRows(r.data)).catch(() => {});
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [invFilter, onlyOpen]);

  const update = async (row, field, value) => {
    try {
      await api.patch(`/inspections/${row.inspection_id}/spare-parts/${row.id}`, { field, value });
      toast.success("Diperbarui");
      load();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Tidak diizinkan");
    }
  };

  return (
    <div className="space-y-5" data-testid="spare-parts">
      <div>
        <p className="overline text-accent">Follow-up Terpusat</p>
        <h1 className="font-head text-2xl font-extrabold tracking-tight text-primary">Tracking Spare Part</h1>
        <p className="text-sm text-muted-foreground">Pantau pergerakan permintaan penggantian lintas tim.</p>
      </div>

      <div className="flex flex-wrap gap-2">
        <select value={invFilter} onChange={(e) => setInvFilter(e.target.value)} data-testid="filter-inventory"
          className="h-9 rounded-md border border-input bg-white px-3 text-sm">
          <option value="">Semua Status Inventory</option>
          {SPARE_FIELDS.inventory_status.options.map((o) => <option key={o.v} value={o.v}>{o.l}</option>)}
        </select>
        <button
          onClick={() => setOnlyOpen((v) => !v)}
          data-testid="toggle-open"
          className={`h-9 rounded-md border px-3 text-sm font-medium ${onlyOpen ? "border-accent bg-accent/10 text-accent" : "border-input bg-white text-slate-600"}`}
        >
          Belum Diganti Saja
        </button>
      </div>

      {rows.length === 0 ? (
        <Card className="flex flex-col items-center gap-2 border-dashed py-16 text-muted-foreground">
          <Wrench size={32} />
          <p className="text-sm">Tidak ada permintaan spare part.</p>
        </Card>
      ) : (
        <Card className="border-border p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-xs">Spare Part</TableHead>
                  <TableHead className="text-xs">Site / Lift</TableHead>
                  <TableHead className="text-xs">Qty</TableHead>
                  {Object.values(SPARE_FIELDS).map((f) => <TableHead key={f.label} className="text-xs">{f.label}</TableHead>)}
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((row) => (
                  <TableRow key={`${row.inspection_id}-${row.id}`} data-testid={`sp-row-${row.id}`}>
                    <TableCell className="text-sm font-semibold text-primary">{row.name}</TableCell>
                    <TableCell className="text-xs">
                      <button onClick={() => navigate(`/inspections/${row.inspection_id}`)} className="text-left hover:text-accent">
                        <span className="block font-medium">{row.site_name}</span>
                        <span className="text-muted-foreground">{row.job_number} · {row.lift_number}</span>
                      </button>
                    </TableCell>
                    <TableCell className="text-sm">{row.quantity || "-"}</TableCell>
                    {Object.entries(SPARE_FIELDS).map(([field, cfg]) => {
                      const canEdit = cfg.roles.includes(user.role) || user.role === "admin";
                      const meta = spareOptionMeta(field, row[field]);
                      return (
                        <TableCell key={field}>
                          {canEdit ? (
                            <select
                              value={row[field]}
                              data-testid={`sp-${row.id}-${field}`}
                              onChange={(e) => update(row, field, e.target.value)}
                              className="rounded-md border border-input bg-white px-1.5 py-1 text-[11px]"
                            >
                              {cfg.options.map((o) => <option key={o.v} value={o.v}>{o.l}</option>)}
                            </select>
                          ) : (
                            <span className={`inline-block whitespace-nowrap rounded px-2 py-1 text-[11px] font-semibold ${meta?.c}`}>{meta?.l}</span>
                          )}
                        </TableCell>
                      );
                    })}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </Card>
      )}
    </div>
  );
}
