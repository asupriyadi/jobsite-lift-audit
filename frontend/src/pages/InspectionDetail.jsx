import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api, { fileUrl, openInspectionPdf } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { STATUSES, judgmentByKey, SPARE_FIELDS, spareOptionMeta } from "@/lib/meta";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import ReportWorkflow from "@/components/ReportWorkflow";
import PhotoUpload from "@/components/PhotoUpload";
import {
  FilePdf, ArrowLeft, Trash, PencilSimple,
} from "@phosphor-icons/react";
import { toast } from "sonner";

const SIR_SIG = [
  { key: "issued_by", label: "Issued By (Teknisi)", roles: ["technician", "supervisor", "head_maintenance"] },
  { key: "customer", label: "Customer", roles: ["customer", "technician", "supervisor", "head_maintenance"] },
  { key: "checked_by", label: "Checked By (Supervisor)", roles: ["supervisor", "head_maintenance"] },
  { key: "approved_by", label: "Approved (Kepala Maint.)", roles: ["head_maintenance"] },
];

export default function InspectionDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [insp, setInsp] = useState(null);

  const load = () => api.get(`/inspections/${id}`).then((r) => setInsp(r.data)).catch(() => {});
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [id]);

  if (!insp) return <div className="text-sm text-muted-foreground">Memuat…</div>;

  const setStatus = async (status) => {
    try {
      await api.patch(`/inspections/${id}/status`, { status });
      toast.success("Status diperbarui");
      load();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Gagal");
    }
  };

  const addSignature = async (key, signature) => {
    try {
      await api.patch(`/inspections/${id}/signature`, { key, signature });
      toast.success("Tanda tangan tersimpan");
      load();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Gagal");
    }
  };

  const updateSpare = async (spareId, field, value) => {
    try {
      await api.patch(`/inspections/${id}/spare-parts/${spareId}`, { field, value });
      load();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Tidak diizinkan");
    }
  };

  const del = async () => {
    if (!window.confirm("Hapus laporan ini?")) return;
    await api.delete(`/inspections/${id}`);
    toast.success("Dihapus");
    navigate("/inspections");
  };

  const sigRoles = [
    ["issued_by", "Issued By (Teknisi)"], ["customer", "Customer"],
    ["checked_by", "Checked By (Supervisor)"], ["approved_by", "Approved (Kepala Maint.)"],
  ];

  return (
    <div className="mx-auto max-w-4xl space-y-5" data-testid="inspection-detail">
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-primary">
        <ArrowLeft size={15} /> Kembali
      </button>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <p className="overline text-accent">SIR · {insp.checklist_type}</p>
            <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${STATUSES[insp.status]?.color}`}>
              {STATUSES[insp.status]?.label}
            </span>
          </div>
          <h1 className="font-head text-2xl font-extrabold tracking-tight text-primary">{insp.site_name}</h1>
          <p className="text-sm text-muted-foreground">{insp.job_number} · Lift {insp.lift_number}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => openInspectionPdf(id)} data-testid="export-pdf">
            <FilePdf size={16} className="mr-1.5" /> Export PDF
          </Button>
          {insp.status === "draft" && (user.id === insp.technician_id || user.role === "admin") && (
            <Button variant="outline" onClick={() => navigate(`/inspections/${id}/edit`)} data-testid="edit-inspection">
              <PencilSimple size={16} className="mr-1.5" /> Edit
            </Button>
          )}
          {["technician", "supervisor", "head_maintenance", "admin"].includes(user.role) && (
            <Button variant="ghost" size="icon" onClick={del} data-testid="delete-inspection" className="text-red-500">
              <Trash size={16} />
            </Button>
          )}
        </div>
      </div>

      {/* Status & signature workflow */}
      <ReportWorkflow status={insp.status} signatures={insp.signatures} user={user}
        onStatus={setStatus} onSign={addSignature} sigConfig={SIR_SIG} />

      {/* Info grid */}
      <Card className="grid grid-cols-2 gap-x-4 gap-y-3 border-border p-5 sm:grid-cols-4">
        {[
          ["Tanggal", insp.inspection_date], ["Waktu", `${insp.time_from}–${insp.time_to}`],
          ["Teknisi", insp.serviced_by], ["Total Unit", insp.total_units],
        ].map(([l, v]) => (
          <div key={l}>
            <p className="overline text-muted-foreground">{l}</p>
            <p className="text-sm font-semibold text-primary">{v}</p>
          </div>
        ))}
      </Card>

      {/* Checklist results */}
      <Card className="border-border p-0">
        <h3 className="font-head border-b border-border p-4 font-bold text-primary">Hasil Checklist</h3>
        <div className="divide-y divide-border">
          {(insp.items || []).map((it) => {
            const j = judgmentByKey(it.judgment);
            return (
              <div key={it.no} className="p-4" data-testid={`detail-item-${it.no}`}>
                <div className="flex items-start gap-2.5">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded bg-slate-500 text-[11px] font-bold text-white">{it.no}</span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm leading-snug text-slate-700">{it.description}</p>
                    <p className="overline mt-0.5 text-slate-400">{it.section}</p>
                  </div>
                  {j ? (
                    <span className={`shrink-0 rounded-md border px-2 py-1 text-[11px] font-semibold ${j.soft} ${j.text}`}>
                      {j.mark} {j.label}
                    </span>
                  ) : <span className="shrink-0 text-[11px] text-slate-300">—</span>}
                </div>
                {it.points?.some((p) => p.measurement || p.photo_file_id) && (
                  <div className="mt-2 flex flex-wrap gap-3 pl-8">
                    {it.points.map((p, i) => (
                      (p.measurement || p.photo_file_id) && (
                        <div key={i} className="flex items-center gap-2 rounded-md border border-border bg-slate-50 p-1.5">
                          {p.photo_file_id && (
                            <img src={fileUrl(p.photo_file_id)} alt="" className="h-12 w-12 rounded object-cover" />
                          )}
                          <div className="text-[11px]">
                            <p className="font-semibold text-slate-500">Titik {p.index}</p>
                            <p className="text-primary">{p.measurement || "-"}</p>
                          </div>
                        </div>
                      )
                    ))}
                  </div>
                )}
                {it.remark && <p className="mt-2 pl-8 text-[12px] italic text-muted-foreground">“{it.remark}”</p>}
              </div>
            );
          })}
        </div>
      </Card>

      {insp.global_remark && (
        <Card className="border-border p-5">
          <p className="overline mb-1 text-muted-foreground">Remark Global</p>
          <p className="text-sm text-slate-700">{insp.global_remark}</p>
        </Card>
      )}

      {/* Spare parts with follow-up */}
      {(insp.spare_parts || []).length > 0 && (
        <Card className="border-border p-5">
          <h3 className="font-head mb-3 font-bold text-primary">Spare Part & Follow-up</h3>
          <div className="space-y-3">
            {insp.spare_parts.map((sp) => (
              <div key={sp.id} className="rounded-lg border border-border p-3" data-testid={`spare-row-${sp.id}`}>
                <div className="mb-2 flex items-center justify-between">
                  <p className="text-sm font-semibold text-primary">{sp.name}</p>
                  <span className="text-xs text-muted-foreground">Qty: {sp.quantity || "-"}</span>
                </div>
                <div className="grid gap-2 sm:grid-cols-4">
                  {Object.entries(SPARE_FIELDS).map(([field, cfg]) => {
                    const canEdit = cfg.roles.includes(user.role) || user.role === "admin";
                    const meta = spareOptionMeta(field, sp[field]);
                    return (
                      <div key={field}>
                        <p className="overline mb-1 text-muted-foreground">{cfg.label}</p>
                        {canEdit ? (
                          <select
                            value={sp[field]}
                            data-testid={`spare-${sp.id}-${field}`}
                            onChange={(e) => updateSpare(sp.id, field, e.target.value)}
                            className="w-full rounded-md border border-input bg-white px-2 py-1.5 text-xs"
                          >
                            {cfg.options.map((o) => <option key={o.v} value={o.v}>{o.l}</option>)}
                          </select>
                        ) : (
                          <span className={`inline-block rounded px-2 py-1 text-[11px] font-semibold ${meta?.c}`}>{meta?.l}</span>
                        )}
                      </div>
                    );
                  })}
                </div>
                <div className="mt-3 flex items-center gap-3 border-t border-border pt-3">
                  <div>
                    <p className="overline mb-1 text-muted-foreground">Foto Setelah Penggantian</p>
                    {(user.role === "technician" || user.role === "troubleshooter" || user.role === "supervisor" || user.role === "head_maintenance" || user.role === "admin") ? (
                      <PhotoUpload testid={`spare-after-${sp.id}`} fileId={sp.after_photo_file_id}
                        onChange={(fid) => updateSpare(sp.id, "after_photo_file_id", fid || "")} />
                    ) : sp.after_photo_file_id ? (
                      <img src={fileUrl(sp.after_photo_file_id)} alt="" className="h-16 w-16 rounded-md border border-border object-cover" />
                    ) : <span className="text-[11px] text-slate-400">Belum ada</span>}
                  </div>
                  {sp.maintenance_status === "replaced" && (
                    <span className="rounded-md bg-emerald-50 px-2 py-1 text-[11px] font-semibold text-emerald-700">Bukti pemasangan</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Signatures */}
      <Card className="border-border p-5">
        <h3 className="font-head mb-3 font-bold text-primary">Tanda Tangan</h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {sigRoles.map(([k, label]) => {
            const s = insp.signatures?.[k] || {};
            return (
              <div key={k} className="rounded-md border border-border p-2 text-center">
                <div className="flex h-16 items-center justify-center rounded bg-slate-50">
                  {s.image ? <img src={s.image} alt={label} className="max-h-16" /> : <span className="text-[10px] text-slate-300">Belum TTD</span>}
                </div>
                <p className="mt-1 text-[11px] font-semibold text-primary">{s.name || "-"}</p>
                <p className="overline text-slate-400">{label}</p>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
