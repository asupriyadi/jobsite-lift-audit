import React, { useState } from "react";
import api, { fileUrl } from "@/lib/api";
import { Camera, SpinnerGap, X } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function PhotoUpload({ fileId, onChange, testid }) {
  const [uploading, setUploading] = useState(false);

  const handle = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const { data } = await api.post("/upload", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      onChange(data.file_id);
    } catch (err) {
      toast.error("Gagal upload foto");
    } finally {
      setUploading(false);
    }
  };

  if (fileId) {
    return (
      <div className="relative h-16 w-16 shrink-0" data-testid={testid}>
        <img src={fileUrl(fileId)} alt="bukti" className="h-16 w-16 rounded-md object-cover border border-border" />
        <button
          type="button"
          onClick={() => onChange(null)}
          data-testid={`${testid}-remove`}
          className="absolute -right-1.5 -top-1.5 rounded-full bg-red-500 p-0.5 text-white shadow"
        >
          <X size={12} weight="bold" />
        </button>
      </div>
    );
  }

  return (
    <label
      data-testid={testid}
      className="flex h-16 w-16 shrink-0 cursor-pointer flex-col items-center justify-center rounded-md border border-dashed border-slate-300 bg-slate-50 text-slate-400 hover:border-accent hover:text-accent transition-colors"
    >
      {uploading ? <SpinnerGap size={20} className="animate-spin" /> : <Camera size={20} />}
      <span className="mt-0.5 text-[9px]">{uploading ? "…" : "Foto"}</span>
      <input type="file" accept="image/*" capture="environment" className="hidden" onChange={handle} />
    </label>
  );
}
