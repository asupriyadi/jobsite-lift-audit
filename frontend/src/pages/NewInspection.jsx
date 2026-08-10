import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api, { apiError } from "@/lib/api";
import { CHECKLIST_TYPES, JUDGMENTS } from "@/lib/meta";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import JudgmentToggle from "@/components/JudgmentToggle";
import PhotoUpload from "@/components/PhotoUpload";
import SignaturePad from "@/components/SignaturePad";
import {
  ArrowRight, ArrowLeft, Plus, Trash, SpinnerGap, Ruler, CheckCircle,
} from "@phosphor-icons/react";
import { toast } from "sonner";

const STEPS = ["Informasi", "Checklist", "Spare Part & Remark", "Tanda Tangan"];

export default function NewInspection() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = !!id;
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [header, setHeader] = useState({
    job_number: "", site_name: "", inspection_date: new Date().toISOString().slice(0, 10),
    time_from: "", time_to: "", serviced_by: "", total_units: "", lift_number: "", checklist_type: "",
  });
  const [items, setItems] = useState([]);
  const [globalRemark, setGlobalRemark] = useState("");
  const [spareParts, setSpareParts] = useState([]);
  const [signatures, setSignatures] = useState({
    issued_by: {}, customer: {}, checked_by: {}, approved_by: {},
  });

  useEffect(() => {
    if (!isEdit) return;
    api.get(`/inspections/${id}`).then(({ data }) => {
      if (data.status !== "draft") {
        toast.error("Laporan sudah dikirim, tidak dapat diedit");
        navigate(`/inspections/${id}`);
        return;
      }
      setHeader({
        job_number: data.job_number || "", site_name: data.site_name || "",
        inspection_date: data.inspection_date || "", time_from: data.time_from || "",
        time_to: data.time_to || "", serviced_by: data.serviced_by || "",
        total_units: String(data.total_units ?? ""), lift_number: data.lift_number || "",
        checklist_type: data.checklist_type || "",
      });
      setItems(data.items || []);
      setGlobalRemark(data.global_remark || "");
      setSpareParts(data.spare_parts || []);
      setSignatures(data.signatures || { issued_by: {}, customer: {}, checked_by: {}, approved_by: {} });
    }).catch(() => toast.error("Gagal memuat laporan"));
    // eslint-disable-next-line
  }, [id]);

  const lookupBuilding = async (jn) => {
    if (!jn || jn.length < 3) return;
    try {
      const { data } = await api.get(`/buildings/lookup?job_number=${encodeURIComponent(jn)}`);
      if (data && data.site_name) {
        setHeader((h) => ({ ...h, site_name: data.site_name }));
        toast.success(`Gedung ditemukan: ${data.site_name}`);
      }
    } catch (e) { /* ignore */ }
  };

  const sections = [...new Set(items.map((i) => i.section))];

  const loadChecklist = async (type) => {
    setHeader((h) => ({ ...h, checklist_type: type }));
    try {
      const { data } = await api.get(`/checklist/master?type=${type}`);
      setItems(
        data.items.map((it) => ({
          ...it,
          judgment: null,
          remark: "",
          points: Array.from({ length: it.photo_points }, (_, idx) => ({
            index: idx + 1, measurement: "", photo_file_id: null,
          })),
        }))
      );
    } catch (e) {
      toast.error("Gagal memuat checklist");
    }
  };

  const setItem = (no, patch) =>
    setItems((prev) => prev.map((it) => (it.no === no ? { ...it, ...patch } : it)));
  const setPoint = (no, idx, patch) =>
    setItems((prev) =>
      prev.map((it) =>
        it.no === no
          ? { ...it, points: it.points.map((p, i) => (i === idx ? { ...p, ...patch } : p)) }
          : it
      )
    );

  const addSpare = () =>
    setSpareParts((s) => [...s, { name: "", quantity: "", note: "" }]);
  const setSpare = (i, patch) =>
    setSpareParts((s) => s.map((sp, idx) => (idx === i ? { ...sp, ...patch } : sp)));
  const delSpare = (i) => setSpareParts((s) => s.filter((_, idx) => idx !== i));

  const validateHeader = () => {
    const req = ["job_number", "site_name", "inspection_date", "time_from", "time_to", "serviced_by", "lift_number", "checklist_type"];
    for (const k of req) if (!header[k]) return false;
    return true;
  };

  const next = () => {
    if (step === 0 && !validateHeader()) {
      toast.error("Lengkapi semua informasi & pilih jenis checklist");
      return;
    }
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  };

  const filled = items.filter((i) => i.judgment).length;
  const allFilled = items.length > 0 && filled === items.length;

  const submit = async (asStatus) => {
    if (asStatus === "submitted" && !allFilled) {
      toast.error("Checklist harus 100% terisi untuk submit. Simpan sebagai draft saja.");
      return;
    }
    setLoading(true);
    try {
      const payload = {
        ...header,
        total_units: parseInt(header.total_units || "0", 10),
        items,
        global_remark: globalRemark,
        spare_parts: spareParts.filter((s) => s.name.trim()),
        signatures,
        status: asStatus,
      };
      const { data } = isEdit
        ? await api.put(`/inspections/${id}`, payload)
        : await api.post("/inspections", payload);
      toast.success(asStatus === "draft" ? "Tersimpan sebagai draft" : "Laporan SIR terkirim");
      navigate(`/inspections/${data.id}`);
    } catch (e) {
      toast.error(apiError(e.response?.data?.detail) || "Gagal menyimpan");
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="mx-auto max-w-4xl space-y-5" data-testid="new-inspection">
      <div>
        <p className="overline text-accent">Formulir SIR</p>
        <h1 className="font-head text-2xl font-extrabold tracking-tight text-primary">{isEdit ? "Edit Inspeksi (Draft)" : "Inspeksi Baru"}</h1>
      </div>

      {/* Stepper */}
      <div className="flex items-center gap-1.5">
        {STEPS.map((s, i) => (
          <div key={s} className="flex flex-1 items-center gap-1.5">
            <div className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-bold ${
              i <= step ? "bg-accent text-white" : "bg-secondary text-slate-400"
            }`}>{i + 1}</div>
            <span className={`hidden text-xs font-medium sm:block ${i === step ? "text-primary" : "text-slate-400"}`}>{s}</span>
            {i < STEPS.length - 1 && <div className={`h-0.5 flex-1 ${i < step ? "bg-accent" : "bg-border"}`} />}
          </div>
        ))}
      </div>

      {/* STEP 0: header */}
      {step === 0 && (
        <Card className="space-y-5 border-border p-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label className="text-xs">Job Number (Pabrik)</Label>
              <Input value={header.job_number} placeholder="ZEZ3624" data-testid="field-job_number"
                onChange={(e) => setHeader({ ...header, job_number: e.target.value })}
                onBlur={(e) => lookupBuilding(e.target.value)} className="mt-1" />
              <p className="mt-1 text-[10px] text-muted-foreground">Nama gedung terisi otomatis dari data master.</p>
            </div>
            <Field label="Site Name (Nama Gedung)" testid="site_name" value={header.site_name} onChange={(v) => setHeader({ ...header, site_name: v })} />
            <Field label="Tanggal Pemeriksaan" testid="inspection_date" type="date" value={header.inspection_date} onChange={(v) => setHeader({ ...header, inspection_date: v })} />
            <Field label="Nama Teknisi" testid="serviced_by" value={header.serviced_by} onChange={(v) => setHeader({ ...header, serviced_by: v })} />
            <Field label="Waktu Mulai" testid="time_from" type="time" value={header.time_from} onChange={(v) => setHeader({ ...header, time_from: v })} />
            <Field label="Waktu Selesai" testid="time_to" type="time" value={header.time_to} onChange={(v) => setHeader({ ...header, time_to: v })} />
            <Field label="Jumlah Total Unit di Jobsite" testid="total_units" type="number" value={header.total_units} onChange={(v) => setHeader({ ...header, total_units: v })} />
            <Field label="Unit yang Diperiksa (Lift No.)" testid="lift_number" value={header.lift_number} onChange={(v) => setHeader({ ...header, lift_number: v })} placeholder="LH1" />
          </div>

          <div>
            <Label className="text-xs">Jenis Checklist Pemeriksaan</Label>
            <div className="mt-2 grid gap-2 sm:grid-cols-3">
              {CHECKLIST_TYPES.map((t) => (
                <button
                  key={t.key}
                  type="button"
                  data-testid={`checklist-type-${t.key}`}
                  onClick={() => loadChecklist(t.key)}
                  className={`rounded-lg border p-3 text-left transition-colors ${
                    header.checklist_type === t.key ? "border-accent bg-accent/5 ring-1 ring-accent" : "border-border bg-white hover:border-slate-300"
                  }`}
                >
                  <p className="font-head font-bold text-primary">{t.key}</p>
                  <p className="text-[11px] text-muted-foreground">{t.desc}</p>
                </button>
              ))}
            </div>
            {header.checklist_type && (
              <p className="mt-2 text-xs text-accent">{items.length} item pemeriksaan dimuat.</p>
            )}
          </div>
        </Card>
      )}

      {/* STEP 1: checklist */}
      {step === 1 && (
        <Card className="border-border p-0">
          <div className="flex items-center justify-between border-b border-border p-4">
            <h3 className="font-head font-bold text-primary">Checklist {header.checklist_type}</h3>
            <span className="text-xs text-muted-foreground">{filled}/{items.length} terisi</span>
          </div>
          <Tabs defaultValue={sections[0]} className="w-full">
            <div className="overflow-x-auto border-b border-border px-2">
              <TabsList className="h-auto flex-nowrap justify-start gap-1 bg-transparent p-2">
                {sections.map((s) => (
                  <TabsTrigger key={s} value={s} data-testid={`tab-${s}`}
                    className="whitespace-nowrap text-[11px] data-[state=active]:bg-primary data-[state=active]:text-white">
                    {s}
                  </TabsTrigger>
                ))}
              </TabsList>
            </div>
            {sections.map((s) => (
              <TabsContent key={s} value={s} className="m-0 divide-y divide-border">
                {items.filter((it) => it.section === s).map((it) => (
                  <div key={it.no} className="p-4" data-testid={`checklist-item-${it.no}`}>
                    <div className="mb-2 flex gap-2.5">
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded bg-primary text-[11px] font-bold text-white">{it.no}</span>
                      <div className="min-w-0">
                        <p className="text-sm leading-snug text-slate-700">{it.description}</p>
                        <p className="mt-0.5 overline text-slate-400">{it.section}</p>
                      </div>
                    </div>
                    <JudgmentToggle testid={`judgment-${it.no}`} value={it.judgment}
                      onChange={(v) => setItem(it.no, { judgment: v })} />

                    {it.photo_points > 0 && (
                      <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 p-3">
                        <p className="mb-2 flex items-center gap-1 text-[11px] font-semibold text-amber-700">
                          <Ruler size={13} /> Wajib ukuran & foto — {it.photo_points} titik
                        </p>
                        <div className="space-y-2">
                          {it.points.map((p, idx) => (
                            <div key={idx} className="flex items-center gap-2">
                              <span className="w-8 shrink-0 text-[11px] font-semibold text-amber-700">#{idx + 1}</span>
                              <Input
                                data-testid={`measure-${it.no}-${idx}`}
                                value={p.measurement}
                                onChange={(e) => setPoint(it.no, idx, { measurement: e.target.value })}
                                placeholder="Ukuran hasil"
                                className="h-9 flex-1 text-sm"
                              />
                              <PhotoUpload testid={`photo-${it.no}-${idx}`} fileId={p.photo_file_id}
                                onChange={(fid) => setPoint(it.no, idx, { photo_file_id: fid })} />
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <Textarea
                      data-testid={`remark-${it.no}`}
                      value={it.remark}
                      onChange={(e) => setItem(it.no, { remark: e.target.value })}
                      placeholder="Remark / keterangan tambahan (khusus ◎ atau ✖)"
                      className="mt-2 min-h-[38px] text-sm"
                    />
                  </div>
                ))}
              </TabsContent>
            ))}
          </Tabs>
        </Card>
      )}

      {/* STEP 2: spare parts + global remark */}
      {step === 2 && (
        <div className="space-y-4">
          <Card className="border-border p-5">
            <h3 className="font-head mb-1 font-bold text-primary">Remark Global</h3>
            <p className="mb-3 text-xs text-muted-foreground">Keterangan / informasi global untuk unit yang diperiksa.</p>
            <Textarea data-testid="global-remark" value={globalRemark} onChange={(e) => setGlobalRemark(e.target.value)}
              placeholder="Kondisi umum unit, temuan penting, rekomendasi…" className="min-h-[90px]" />
          </Card>

          <Card className="border-border p-5">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h3 className="font-head font-bold text-primary">Spare Part Diperlukan</h3>
                <p className="text-xs text-muted-foreground">Nama & jumlah untuk penggantian / pengadaan.</p>
              </div>
              <Button type="button" size="sm" variant="outline" onClick={addSpare} data-testid="add-spare">
                <Plus size={14} className="mr-1" /> Tambah
              </Button>
            </div>
            {spareParts.length === 0 && (
              <p className="py-6 text-center text-sm text-muted-foreground">Belum ada spare part ditambahkan.</p>
            )}
            <div className="space-y-2">
              {spareParts.map((sp, i) => (
                <div key={i} className="flex items-start gap-2 rounded-md border border-border p-2" data-testid={`spare-${i}`}>
                  <Input value={sp.name} onChange={(e) => setSpare(i, { name: e.target.value })}
                    data-testid={`spare-name-${i}`} placeholder="Nama spare part" className="h-9 flex-1 text-sm" />
                  <Input value={sp.quantity} onChange={(e) => setSpare(i, { quantity: e.target.value })}
                    data-testid={`spare-qty-${i}`} placeholder="Qty" className="h-9 w-20 text-sm" />
                  <Button type="button" size="icon" variant="ghost" onClick={() => delSpare(i)}
                    data-testid={`spare-del-${i}`} className="h-9 w-9 text-red-500">
                    <Trash size={15} />
                  </Button>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* STEP 3: signatures */}
      {step === 3 && (
        <Card className="border-border p-5">
          <h3 className="font-head mb-3 font-bold text-primary">Tanda Tangan</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            <SignaturePad testid="sig-issued" label="Issued By (Teknisi)" value={signatures.issued_by}
              onChange={(v) => setSignatures((s) => ({ ...s, issued_by: v }))} />
            <SignaturePad testid="sig-customer" label="Customer" value={signatures.customer}
              onChange={(v) => setSignatures((s) => ({ ...s, customer: v }))} />
            <SignaturePad testid="sig-checked" label="Checked By (Supervisor)" value={signatures.checked_by}
              onChange={(v) => setSignatures((s) => ({ ...s, checked_by: v }))} />
            <SignaturePad testid="sig-approved" label="Approved By (Kepala Maint.)" value={signatures.approved_by}
              onChange={(v) => setSignatures((s) => ({ ...s, approved_by: v }))} />
          </div>
          <div className="mt-4 flex flex-col gap-2 sm:flex-row">
            <Button variant="outline" disabled={loading} onClick={() => submit("draft")} data-testid="save-draft" className="flex-1">
              Simpan Draft
            </Button>
            <Button disabled={loading || !allFilled} onClick={() => submit("submitted")} data-testid="submit-sir"
              className="flex-1 bg-emerald-600 hover:bg-emerald-700">
              {loading ? <SpinnerGap size={16} className="mr-2 animate-spin" /> : <CheckCircle size={16} className="mr-2" />}
              Submit Laporan SIR
            </Button>
          </div>
          {!allFilled && (
            <p className="mt-2 text-center text-xs text-amber-600" data-testid="submit-warning">
              Checklist belum 100% terisi ({filled}/{items.length}). Submit dinonaktifkan — simpan sebagai draft dulu.
            </p>
          )}
        </Card>
      )}

      {/* nav */}
      <div className="flex justify-between">
        <Button variant="ghost" onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0} data-testid="step-back">
          <ArrowLeft size={16} className="mr-1" /> Kembali
        </Button>
        {step < STEPS.length - 1 && (
          <Button onClick={next} data-testid="step-next" className="bg-primary hover:bg-primary/90">
            Lanjut <ArrowRight size={16} className="ml-1" />
          </Button>
        )}
      </div>
    </div>
  );
}

function Field({ label, value, onChange, type = "text", placeholder, testid }) {
  return (
    <div>
      <Label className="text-xs">{label}</Label>
      <Input type={type} value={value} placeholder={placeholder} data-testid={`field-${testid}`}
        onChange={(e) => onChange(e.target.value)} className="mt-1" />
    </div>
  );
}
