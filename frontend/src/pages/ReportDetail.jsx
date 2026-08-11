import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api, { fileUrl, openReportPdf } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { STATUSES } from "@/lib/meta";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import ReportWorkflow from "@/components/ReportWorkflow";
import { FilePdf, ArrowLeft, Trash, PencilSimple } from "@phosphor-icons/react";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ECR_SIG = [
  { key: "customer", label: "Customer", roles: ["customer", "technician", "supervisor", "head_maintenance"] },
  { key: "issuer", label: "Issuer (Teknisi)", roles: ["technician", "supervisor", "head_maintenance"] },
  { key: "checker", label: "Checker (Supervisor)", roles: ["supervisor", "head_maintenance"] },
  { key: "approver", label: "Approver (Kepala Maint.)", roles: ["head_maintenance"] },
];
const HOR_SIG = [
  { key: "fujitec_rep", label: "PT. Fujitec Indonesia", roles: ["technician", "supervisor", "head_maintenance"] },
  { key: "customer", label: "Customer / Building", roles: ["customer", "technician", "supervisor", "head_maintenance"] },
];

export default function ReportDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [rep, setRep] = useState(null);

  const load = () => api.get(`/reports/${id}`).then((r) => setRep(r.data)).catch(() => {});
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [id]);
  if (!rep) return <div className="text-sm text-muted-foreground">Memuat…</div>;

  const isECR = rep.report_type === "ECR";
  const sigConfig = isECR ? ECR_SIG : HOR_SIG;

  const onStatus = async (status) => {
    try { await api.patch(`/reports/${id}/status`, { status }); toast.success("Status diperbarui"); load(); }
    catch (e) { toast.error(e.response?.data?.detail || "Gagal"); }
  };
  const onSign = async (key, signature) => {
    try { await api.patch(`/reports/${id}/signature`, { key, signature }); toast.success("Tanda tangan tersimpan"); load(); }
    catch (e) { toast.error(e.response?.data?.detail || "Gagal"); }
  };
  const del = async () => {
    if (!window.confirm("Hapus laporan ini?")) return;
    await api.delete(`/reports/${id}`); toast.success("Dihapus"); navigate("/reports");
  };

  const editPath = isECR ? `/reports/ecr/${id}/edit` : `/reports/hor/${id}/edit`;

  return (
    <div className="mx-auto max-w-3xl space-y-5" data-testid="report-detail">
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-primary">
        <ArrowLeft size={15} /> Kembali
      </button>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <p className="overline text-accent">{rep.report_type} · {isECR ? "Call Back" : "Hand Over"}</p>
            <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${STATUSES[rep.status]?.color}`}>{STATUSES[rep.status]?.label}</span>
          </div>
          <h1 className="font-head text-2xl font-extrabold tracking-tight text-primary">{rep.site_name || "-"}</h1>
          <p className="text-sm text-muted-foreground">{rep.job_number} · {rep.unit_no || rep.lift_number}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => openReportPdf(id)} data-testid="report-export-pdf"><FilePdf size={16} className="mr-1.5" /> Export PDF</Button>
          {rep.status === "draft" && (user.id === rep.technician_id || user.role === "admin") && (
            <Button variant="outline" onClick={() => navigate(editPath)} data-testid="report-edit"><PencilSimple size={16} className="mr-1.5" /> Edit</Button>
          )}
          {["technician", "supervisor", "head_maintenance", "admin"].includes(user.role) && (
            <Button variant="ghost" size="icon" onClick={del} data-testid="report-delete" className="text-red-500"><Trash size={16} /></Button>
          )}
        </div>
      </div>

      <ReportWorkflow status={rep.status} signatures={rep.signatures} user={user} onStatus={onStatus} onSign={onSign} sigConfig={sigConfig} />

      {isECR ? (
        <>
          <Card className="grid grid-cols-2 gap-x-4 gap-y-3 border-border p-5 sm:grid-cols-3">
            {[["Technician", rep.technician], ["Unit No", rep.unit_no], ["Tanggal", rep.report_date],
              ["Waktu", `${rep.time_from || ""}–${rep.time_to || ""}`], ["Billing", rep.billing], ["Status Kerja", rep.work_status]].map(([l, v]) => (
              <div key={l}><p className="overline text-muted-foreground">{l}</p><p className="text-sm font-semibold text-primary">{v || "-"}</p></div>
            ))}
          </Card>
          <Card className="space-y-3 border-border p-5">
            {[["Working Details", rep.working_details], ["E/C", rep.ec], ["Action", rep.action], ["Cause", rep.cause], ["Solution", rep.solution]].map(([l, v]) => (
              <div key={l}><p className="overline text-slate-500">{l}</p><p className="whitespace-pre-wrap text-sm text-slate-700">{v || "-"}</p></div>
            ))}
          </Card>
          {(rep.photo_file_ids || []).length > 0 && (
            <Card className="border-border p-5">
              <p className="overline mb-2 text-slate-500">Foto</p>
              <div className="flex flex-wrap gap-2">
                {rep.photo_file_ids.map((fid) => <img key={fid} src={fileUrl(fid)} alt="" className="h-20 w-20 rounded-md border border-border object-cover" />)}
              </div>
            </Card>
          )}
        </>
      ) : (
        <>
          <Card className="grid grid-cols-2 gap-x-4 gap-y-3 border-border p-5 sm:grid-cols-3">
            {[["Lift / Unit", rep.lift_number], ["Tanggal", rep.report_date], ["Job No", rep.job_number]].map(([l, v]) => (
              <div key={l}><p className="overline text-muted-foreground">{l}</p><p className="text-sm font-semibold text-primary">{v || "-"}</p></div>
            ))}
          </Card>
          <PartsCard title="Spare Part Diganti (Baru)" parts={rep.parts_replaced} withPhoto />
          <PartsCard title="Barang Bekas Diserahkan ke Gedung" parts={rep.parts_handover} />
          <PartsCard title="Barang Dikembalikan ke Fujitec" parts={rep.parts_returned} />
          {rep.note && <Card className="border-border p-5"><p className="overline mb-1 text-slate-500">Catatan</p><p className="text-sm text-slate-700">{rep.note}</p></Card>}
        </>
      )}

      <Card className="border-border p-5">
        <h3 className="font-head mb-3 font-bold text-primary">Tanda Tangan</h3>
        <div className={`grid gap-3 ${sigConfig.length > 2 ? "grid-cols-2 sm:grid-cols-4" : "grid-cols-2"}`}>
          {sigConfig.map((c) => {
            const s = rep.signatures?.[c.key] || {};
            return (
              <div key={c.key} className="rounded-md border border-border p-2 text-center">
                <div className="flex h-16 items-center justify-center rounded bg-slate-50">
                  {s.image ? <img src={s.image} alt={c.label} className="max-h-16" /> : <span className="text-[10px] text-slate-300">Belum TTD</span>}
                </div>
                <p className="mt-1 text-[11px] font-semibold text-primary">{s.name || "-"}</p>
                <p className="overline text-slate-400">{c.label}</p>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}

function PartsCard({ title, parts, withPhoto }) {
  return (
    <Card className="border-border p-5">
      <h3 className="font-head mb-2 font-bold text-primary">{title}</h3>
      {(!parts || parts.length === 0) ? <p className="text-xs text-muted-foreground">-</p> : (
        <div className="space-y-2">
          {parts.map((p, i) => (
            <div key={i} className="flex items-center gap-3 rounded-md border border-border p-2">
              <div className="flex-1"><p className="text-sm font-semibold text-primary">{p.name}</p><p className="text-[11px] text-muted-foreground">Qty: {p.qty || "-"}</p></div>
              {withPhoto && (
                <div className="flex gap-2">
                  {p.before_photo_file_id && <div className="text-center"><img src={fileUrl(p.before_photo_file_id)} alt="" className="h-14 w-14 rounded object-cover" /><span className="text-[9px] text-slate-400">Sebelum</span></div>}
                  {p.after_photo_file_id && <div className="text-center"><img src={fileUrl(p.after_photo_file_id)} alt="" className="h-14 w-14 rounded object-cover" /><span className="text-[9px] text-slate-400">Sesudah</span></div>}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
