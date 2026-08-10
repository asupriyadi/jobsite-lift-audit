import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api, { apiError } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import SignaturePad from "@/components/SignaturePad";
import PhotoUpload from "@/components/PhotoUpload";
import { SpinnerGap, CheckCircle } from "@phosphor-icons/react";
import { toast } from "sonner";

const BILLING = [
  { v: "paid", l: "Paid" },
  { v: "free", l: "Free" },
  { v: "include_contract", l: "Include Contract" },
];

export default function NewECR() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = !!id;
  const [loading, setLoading] = useState(false);
  const [f, setF] = useState({
    report_type: "ECR", technician: "", site_name: "", unit_no: "", job_number: "",
    report_date: new Date().toISOString().slice(0, 10), time_from: "", time_to: "",
    working_details: "", ec: "", action: "", cause: "", solution: "", work_status: "",
    billing: "include_contract", photo_file_ids: [],
    signatures: { customer: {}, issuer: {}, checker: {}, approver: {} },
  });
  const set = (k, v) => setF((s) => ({ ...s, [k]: v }));

  useEffect(() => {
    if (!isEdit) return;
    api.get(`/reports/${id}`).then(({ data }) => {
      if (data.status !== "draft") { toast.error("Laporan sudah dikirim, tidak dapat diedit"); navigate(`/reports/${id}`); return; }
      setF({ ...f, ...data, signatures: data.signatures || f.signatures, photo_file_ids: data.photo_file_ids || [] });
    }).catch(() => toast.error("Gagal memuat"));
    // eslint-disable-next-line
  }, [id]);

  const lookupBuilding = async (jn) => {
    if (!jn || jn.length < 3) return;
    try {
      const { data } = await api.get(`/buildings/lookup?job_number=${encodeURIComponent(jn)}`);
      if (data?.site_name) { set("site_name", data.site_name); toast.success(`Gedung: ${data.site_name}`); }
    } catch (e) { /* ignore */ }
  };

  const addPhoto = (fid) => set("photo_file_ids", [...f.photo_file_ids, fid]);
  const rmPhoto = (i) => set("photo_file_ids", f.photo_file_ids.filter((_, idx) => idx !== i));

  const submit = async (status) => {
    if (status === "submitted" && (!f.technician || !f.site_name || !f.unit_no || !f.working_details)) {
      toast.error("Lengkapi Technician, Site, Unit No, dan Working Details untuk submit"); return;
    }
    setLoading(true);
    try {
      const payload = { ...f, status };
      const { data } = isEdit ? await api.put(`/reports/${id}`, payload) : await api.post("/reports", payload);
      toast.success(status === "draft" ? "Tersimpan sebagai draft" : "Laporan ECR terkirim");
      navigate(`/reports/${data.id}`);
    } catch (e) {
      toast.error(apiError(e.response?.data?.detail) || "Gagal menyimpan");
    } finally { setLoading(false); }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-5" data-testid="new-ecr">
      <div>
        <p className="overline text-amber-600">Call Back Report</p>
        <h1 className="font-head text-2xl font-extrabold tracking-tight text-primary">{isEdit ? "Edit ECR (Draft)" : "Work Report / ECR Baru"}</h1>
      </div>

      <Card className="space-y-4 border-border p-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <Label className="text-xs">Job Number</Label>
            <Input value={f.job_number} data-testid="ecr-job_number" placeholder="EX3155"
              onChange={(e) => set("job_number", e.target.value)} onBlur={(e) => lookupBuilding(e.target.value)} className="mt-1" />
          </div>
          <Fld label="Site Name" v={f.site_name} on={(v) => set("site_name", v)} t="site_name" />
          <Fld label="Technician" v={f.technician} on={(v) => set("technician", v)} t="technician" />
          <Fld label="Unit No" v={f.unit_no} on={(v) => set("unit_no", v)} t="unit_no" placeholder="AS201" />
          <Fld label="Tanggal" type="date" v={f.report_date} on={(v) => set("report_date", v)} t="report_date" />
          <div className="grid grid-cols-2 gap-2">
            <Fld label="Mulai" type="time" v={f.time_from} on={(v) => set("time_from", v)} t="time_from" />
            <Fld label="Selesai" type="time" v={f.time_to} on={(v) => set("time_to", v)} t="time_to" />
          </div>
        </div>
        <div>
          <Label className="text-xs">Billing</Label>
          <div className="mt-1 flex gap-2">
            {BILLING.map((b) => (
              <button key={b.v} type="button" data-testid={`ecr-billing-${b.v}`} onClick={() => set("billing", b.v)}
                className={`flex-1 rounded-md border px-3 py-2 text-xs font-medium ${f.billing === b.v ? "border-accent bg-accent/10 text-accent" : "border-border bg-white text-slate-600"}`}>
                {b.l}
              </button>
            ))}
          </div>
        </div>
      </Card>

      <Card className="space-y-3 border-border p-5">
        <Area label="Working Details / Description" v={f.working_details} on={(v) => set("working_details", v)} t="working_details" />
        <Fld label="E/C (Error Code)" v={f.ec} on={(v) => set("ec", v)} t="ec" placeholder="08, 72, 8C, E9" />
        <Area label="Action" v={f.action} on={(v) => set("action", v)} t="action" />
        <Area label="Cause" v={f.cause} on={(v) => set("cause", v)} t="cause" />
        <Area label="Solution" v={f.solution} on={(v) => set("solution", v)} t="solution" />
        <Fld label="Status Pekerjaan" v={f.work_status} on={(v) => set("work_status", v)} t="work_status" placeholder="Close - lift running" />
      </Card>

      <Card className="border-border p-5">
        <Label className="text-xs">Foto (opsional)</Label>
        <div className="mt-2 flex flex-wrap gap-2" data-testid="ecr-photos">
          {f.photo_file_ids.map((fid, i) => (
            <PhotoUpload key={fid} testid={`ecr-photo-${i}`} fileId={fid} onChange={() => rmPhoto(i)} />
          ))}
          <PhotoUpload testid="ecr-photo-add" fileId={null} onChange={addPhoto} />
        </div>
      </Card>

      <Card className="border-border p-5">
        <h3 className="font-head mb-3 font-bold text-primary">Tanda Tangan</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          <SignaturePad testid="ecr-sig-customer" label="Customer" value={f.signatures.customer} onChange={(v) => set("signatures", { ...f.signatures, customer: v })} />
          <SignaturePad testid="ecr-sig-issuer" label="Issuer (Teknisi)" value={f.signatures.issuer} onChange={(v) => set("signatures", { ...f.signatures, issuer: v })} />
        </div>
        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <Button variant="outline" disabled={loading} onClick={() => submit("draft")} data-testid="ecr-save-draft" className="flex-1">Simpan Draft</Button>
          <Button disabled={loading} onClick={() => submit("submitted")} data-testid="ecr-submit" className="flex-1 bg-emerald-600 hover:bg-emerald-700">
            {loading ? <SpinnerGap size={16} className="mr-2 animate-spin" /> : <CheckCircle size={16} className="mr-2" />} Submit ECR
          </Button>
        </div>
      </Card>
    </div>
  );
}

function Fld({ label, v, on, t, type = "text", placeholder }) {
  return (
    <div>
      <Label className="text-xs">{label}</Label>
      <Input type={type} value={v} placeholder={placeholder} data-testid={`ecr-${t}`} onChange={(e) => on(e.target.value)} className="mt-1" />
    </div>
  );
}
function Area({ label, v, on, t }) {
  return (
    <div>
      <Label className="text-xs">{label}</Label>
      <Textarea value={v} data-testid={`ecr-${t}`} onChange={(e) => on(e.target.value)} className="mt-1 min-h-[60px]" />
    </div>
  );
}
