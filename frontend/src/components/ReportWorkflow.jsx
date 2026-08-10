import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import SignaturePad from "@/components/SignaturePad";
import { CheckCircle, SealCheck, ArrowUUpLeft, PaperPlaneTilt } from "@phosphor-icons/react";

const canSet = (target, current, role) => {
  if (role === "admin") return true;
  if (target === "submitted") return ["technician", "supervisor", "head_maintenance"].includes(role);
  if (target === "approved") return role === "head_maintenance";
  if (target === "checked" || target === "draft") {
    if (current === "approved") return role === "head_maintenance";
    return ["supervisor", "head_maintenance"].includes(role);
  }
  return false;
};

export default function ReportWorkflow({ status, signatures, user, onStatus, onSign, sigConfig }) {
  const [drafts, setDrafts] = useState({});

  const transitions = [
    { to: "submitted", label: "Submit", icon: PaperPlaneTilt, cls: "bg-blue-600 hover:bg-blue-700", show: status === "draft" },
    { to: "checked", label: "Tandai Checked", icon: CheckCircle, cls: "bg-amber-500 hover:bg-amber-600", show: status === "submitted" || status === "approved" },
    { to: "approved", label: "Approve", icon: SealCheck, cls: "bg-emerald-600 hover:bg-emerald-700", show: status === "checked" },
    { to: "draft", label: "Turunkan ke Draft", icon: ArrowUUpLeft, cls: "bg-slate-500 hover:bg-slate-600", show: status !== "draft" },
  ].filter((t) => t.show && canSet(t.to, status, user.role));

  const mySignable = sigConfig.filter((c) => (c.roles.includes(user.role) || user.role === "admin") && !signatures?.[c.key]?.image);

  return (
    <Card className="space-y-3 border-border p-4" data-testid="report-workflow">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-muted-foreground">Aksi status:</span>
        {transitions.length === 0 && <span className="text-xs text-slate-400">Tidak ada aksi untuk peran Anda.</span>}
        {transitions.map((t) => (
          <Button key={t.to} size="sm" className={t.cls} data-testid={`status-${t.to}`} onClick={() => onStatus(t.to)}>
            <t.icon size={14} className="mr-1" /> {t.label}
          </Button>
        ))}
      </div>

      {mySignable.length > 0 && (
        <div className="border-t border-border pt-3">
          <p className="overline mb-2 text-accent">Tambahkan Tanda Tangan Anda</p>
          <div className="grid gap-3 sm:grid-cols-2">
            {mySignable.map((c) => (
              <div key={c.key}>
                <SignaturePad testid={`add-sig-${c.key}`} label={c.label}
                  value={drafts[c.key] || {}} onChange={(v) => setDrafts((d) => ({ ...d, [c.key]: v }))} />
                <Button size="sm" variant="outline" className="mt-1 w-full" data-testid={`save-sig-${c.key}`}
                  disabled={!drafts[c.key]?.image}
                  onClick={() => onSign(c.key, drafts[c.key])}>
                  Simpan Tanda Tangan {c.label}
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}
