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
import { SpinnerGap, CheckCircle, Plus, Trash } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function NewHOR() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = !!id;
  const [loading, setLoading] = useState(false);
  const [f, setF] = useState({
    report_type: "HOR", site_name: "", lift_number: "", job_number: "",
    report_date: new Date().toISOString().slice(0, 10), note: "",
    parts_replaced: [{ name: "", qty: "", before_photo_file_id: null, after_photo_file_id: null }],
    parts_handover: [], parts_returned: [],
    signatures: { fujitec_rep: {}, customer: {} },
  });
  const set = (k, v) => setF((s) => ({ ...s, [k]: v }));

  useEffect(() => {
    if (!isEdit) return;
    api.get(`/reports/${id}`).then(({ data }) => {
      if (data.status !== "draft") { toast.error("Laporan sudah dikirim, tidak dapat diedit"); navigate(`/reports/${id}`); return; }
      setF((s) => ({ ...s, ...data, signatures: data.signatures || s.signatures }));
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

  const editList = (key, i, patch) => set(key, f[key].map((p, idx) => (idx === i ? { ...p, ...patch } : p)));
  const addList = (key, withPhoto) => set(key, [...f[key], withPhoto ? { name: "", qty: "", before_photo_file_id: null, after_photo_file_id: null } : { name: "", qty: "" }]);
  const delList = (key, i) => set(key, f[key].filter((_, idx) => idx !== i));

  const submit = async (status) => {
    if (status === "submitted" && (!f.site_name || !f.lift_number)) { toast.error("Lengkapi Site & Lift No untuk submit"); return; }
    setLoading(true);
    try {
      const payload = { ...f, parts_replaced: f.parts_replaced.filter((p) => p.name.trim()) };
      const { data } = isEdit ? await api.put(`/reports/${id}`, { ...payload, status }) : await api.post("/reports", { ...payload, status });
      toast.success(status === "draft" ? "Tersimpan sebagai draft" : "Laporan HOR terkirim");
      navigate(`/reports/${data.id}`);
    } catch (e) { toast.error(apiError(e.response?.data?.detail) || "Gagal menyimpan"); }
    finally { setLoading(false); }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-5" data-testid="new-hor">
      <div>
        <p className="overline text-emerald-600">Hand Over Report</p>
        <h1 className="font-head text-2xl font-extrabold tracking-tight text-primary">{isEdit ? "Edit HOR (Draft)" : "Hand Over Report Baru"}</h1>
      </div>

      <Card className="grid gap-4 border-border p-5 sm:grid-cols-2">
        <div>
          <Label className="text-xs">Job Number</Label>
          <Input value={f.job_number} data-testid="hor-job_number" onChange={(e) => set("job_number", e.target.value)} onBlur={(e) => lookupBuilding(e.target.value)} className="mt-1" />
        </div>
        <div><Label className="text-xs">Building / Site</Label><Input value={f.site_name} data-testid="hor-site_name" onChange={(e) => set("site_name", e.target.value)} className="mt-1" /></div>
        <div><Label className="text-xs">Lift / Unit No</Label><Input value={f.lift_number} data-testid="hor-lift_number" onChange={(e) => set("lift_number", e.target.value)} className="mt-1" placeholder="Escalator L2.1" /></div>
        <div><Label className="text-xs">Tanggal</Label><Input type="date" value={f.report_date} data-testid="hor-report_date" onChange={(e) => set("report_date", e.target.value)} className="mt-1" /></div>
      </Card>

      <Card className="border-border p-5">
        <div className="mb-3 flex items-center justify-between">
          <div><h3 className="font-head font-bold text-primary">Spare Part Diganti (Baru)</h3><p className="text-xs text-muted-foreground">Lampirkan foto sebelum & sesudah penggantian.</p></div>
          <Button type="button" size="sm" variant="outline" onClick={() => addList("parts_replaced", true)} data-testid="hor-add-replaced"><Plus size={14} className="mr-1" /> Tambah</Button>
        </div>
        <div className="space-y-3">
          {f.parts_replaced.map((p, i) => (
            <div key={i} className="rounded-md border border-border p-3" data-testid={`hor-replaced-${i}`}>
              <div className="flex gap-2">
                <Input value={p.name} placeholder="Nama spare part" data-testid={`hor-replaced-name-${i}`} onChange={(e) => editList("parts_replaced", i, { name: e.target.value })} className="h-9 flex-1 text-sm" />
                <Input value={p.qty} placeholder="Qty" data-testid={`hor-replaced-qty-${i}`} onChange={(e) => editList("parts_replaced", i, { qty: e.target.value })} className="h-9 w-24 text-sm" />
                <Button type="button" size="icon" variant="ghost" onClick={() => delList("parts_replaced", i)} className="h-9 w-9 text-red-500"><Trash size={15} /></Button>
              </div>
              <div className="mt-2 flex gap-4">
                <div className="text-center"><p className="mb-1 text-[10px] font-semibold text-slate-500">Sebelum</p><PhotoUpload testid={`hor-before-${i}`} fileId={p.before_photo_file_id} onChange={(fid) => editList("parts_replaced", i, { before_photo_file_id: fid })} /></div>
                <div className="text-center"><p className="mb-1 text-[10px] font-semibold text-slate-500">Sesudah</p><PhotoUpload testid={`hor-after-${i}`} fileId={p.after_photo_file_id} onChange={(fid) => editList("parts_replaced", i, { after_photo_file_id: fid })} /></div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <PartsSimple title="Barang Bekas Diserahkan ke Gedung" k="parts_handover" list={f.parts_handover} addList={addList} editList={editList} delList={delList} />
      <PartsSimple title="Barang Dikembalikan ke Fujitec" k="parts_returned" list={f.parts_returned} addList={addList} editList={editList} delList={delList} />

      <Card className="border-border p-5">
        <Label className="text-xs">Catatan</Label>
        <Textarea value={f.note} data-testid="hor-note" onChange={(e) => set("note", e.target.value)} className="mt-1 min-h-[50px]" />
      </Card>

      <Card className="border-border p-5">
        <h3 className="font-head mb-3 font-bold text-primary">Tanda Tangan</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          <SignaturePad testid="hor-sig-fujitec" label="PT. Fujitec Indonesia" value={f.signatures.fujitec_rep} onChange={(v) => set("signatures", { ...f.signatures, fujitec_rep: v })} />
          <SignaturePad testid="hor-sig-customer" label="Customer / Building" value={f.signatures.customer} onChange={(v) => set("signatures", { ...f.signatures, customer: v })} />
        </div>
        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <Button variant="outline" disabled={loading} onClick={() => submit("draft")} data-testid="hor-save-draft" className="flex-1">Simpan Draft</Button>
          <Button disabled={loading} onClick={() => submit("submitted")} data-testid="hor-submit" className="flex-1 bg-emerald-600 hover:bg-emerald-700">
            {loading ? <SpinnerGap size={16} className="mr-2 animate-spin" /> : <CheckCircle size={16} className="mr-2" />} Submit HOR
          </Button>
        </div>
      </Card>
    </div>
  );
}

function PartsSimple({ title, k, list, addList, editList, delList }) {
  return (
    <Card className="border-border p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-head font-bold text-primary">{title}</h3>
        <Button type="button" size="sm" variant="outline" onClick={() => addList(k, false)} data-testid={`add-${k}`}><Plus size={14} className="mr-1" /> Tambah</Button>
      </div>
      {list.length === 0 && <p className="py-3 text-center text-xs text-muted-foreground">Belum ada.</p>}
      <div className="space-y-2">
        {list.map((p, i) => (
          <div key={i} className="flex gap-2" data-testid={`${k}-${i}`}>
            <Input value={p.name} placeholder="Nama spare part" onChange={(e) => editList(k, i, { name: e.target.value })} className="h-9 flex-1 text-sm" />
            <Input value={p.qty} placeholder="Qty" onChange={(e) => editList(k, i, { qty: e.target.value })} className="h-9 w-24 text-sm" />
            <Button type="button" size="icon" variant="ghost" onClick={() => delList(k, i)} className="h-9 w-9 text-red-500"><Trash size={15} /></Button>
          </div>
        ))}
      </div>
    </Card>
  );
}
