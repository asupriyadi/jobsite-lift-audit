import React from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { ClipboardText, PhoneCall, HandArrowDown, ArrowRight } from "@phosphor-icons/react";

const OPTIONS = [
  {
    key: "SIR", full: "Service Inspection Report", path: "/inspections/new",
    icon: ClipboardText, accent: "bg-blue-600",
    desc: "Pemeriksaan rutin bulanan (1M / 3M / 12M) untuk unit dengan kontrak maintenance sesuai jadwal.",
    trigger: "Trigger: jadwal rutin bulanan",
  },
  {
    key: "ECR", full: "Call Back Report", path: "/reports/ecr/new",
    icon: PhoneCall, accent: "bg-amber-600",
    desc: "Laporan tindak lanjut panggilan/keluhan pelanggan atas permasalahan unit di luar jadwal rutin.",
    trigger: "Trigger: panggilan / info pelanggan",
  },
  {
    key: "HOR", full: "Hand Over Report", path: "/reports/hor/new",
    icon: HandArrowDown, accent: "bg-emerald-600",
    desc: "Serah terima pemasangan / penggantian spare part dengan foto sebelum & sesudah.",
    trigger: "Trigger: pengiriman barang / pemasangan",
  },
];

export default function NewReportChooser() {
  const navigate = useNavigate();
  return (
    <div className="space-y-5" data-testid="report-chooser">
      <div>
        <p className="overline text-accent">Buat Laporan</p>
        <h1 className="font-head text-2xl font-extrabold tracking-tight text-primary">Pilih Jenis Laporan</h1>
        <p className="text-sm text-muted-foreground">Pilih formulir sesuai jenis pekerjaan di jobsite.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {OPTIONS.map((o) => (
          <Card
            key={o.key}
            onClick={() => navigate(o.path)}
            data-testid={`choose-${o.key}`}
            className="group cursor-pointer border-border p-5 transition-all hover:-translate-y-0.5 hover:border-accent hover:shadow-md"
          >
            <div className={`mb-4 flex h-11 w-11 items-center justify-center rounded-lg ${o.accent} text-white`}>
              <o.icon size={22} weight="bold" />
            </div>
            <p className="font-head text-xl font-extrabold text-primary">{o.key}</p>
            <p className="text-sm font-semibold text-slate-600">{o.full}</p>
            <p className="mt-2 text-xs text-muted-foreground">{o.desc}</p>
            <div className="mt-4 flex items-center justify-between border-t border-border pt-3">
              <span className="text-[11px] font-medium text-slate-400">{o.trigger}</span>
              <ArrowRight size={16} className="text-accent transition-transform group-hover:translate-x-1" />
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
