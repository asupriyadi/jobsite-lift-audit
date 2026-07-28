import React, { useRef, useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Eraser } from "@phosphor-icons/react";

export default function SignaturePad({ label, value, onChange, testid }) {
  const canvasRef = useRef(null);
  const drawing = useRef(false);
  const [name, setName] = useState(value?.name || "");
  const hasImage = !!value?.image;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    ctx.strokeStyle = "#0A2540";
    ctx.lineWidth = 2;
    ctx.lineCap = "round";
    if (value?.image) {
      const img = new Image();
      img.onload = () => ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      img.src = value.image;
    }
    // eslint-disable-next-line
  }, []);

  const pos = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const t = e.touches ? e.touches[0] : e;
    return { x: t.clientX - rect.left, y: t.clientY - rect.top };
  };
  const start = (e) => {
    e.preventDefault();
    drawing.current = true;
    const ctx = canvasRef.current.getContext("2d");
    const p = pos(e);
    ctx.beginPath();
    ctx.moveTo(p.x, p.y);
  };
  const move = (e) => {
    if (!drawing.current) return;
    e.preventDefault();
    const ctx = canvasRef.current.getContext("2d");
    const p = pos(e);
    ctx.lineTo(p.x, p.y);
    ctx.stroke();
  };
  const end = () => {
    if (!drawing.current) return;
    drawing.current = false;
    commit(name);
  };
  const commit = (nm) => {
    const image = canvasRef.current.toDataURL("image/png");
    onChange({ name: nm, image, signed_at: new Date().toISOString() });
  };
  const clear = () => {
    const ctx = canvasRef.current.getContext("2d");
    ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    onChange({ name, image: "", signed_at: null });
  };

  return (
    <div className="rounded-lg border border-border bg-white p-3" data-testid={testid}>
      <p className="overline text-muted-foreground mb-2">{label}</p>
      <Input
        placeholder="Nama"
        value={name}
        data-testid={`${testid}-name`}
        onChange={(e) => {
          setName(e.target.value);
          onChange({ ...(value || {}), name: e.target.value });
        }}
        className="mb-2 h-9 text-sm"
      />
      <div className="relative rounded-md border border-dashed border-slate-300 bg-slate-50">
        <canvas
          ref={canvasRef}
          width={320}
          height={110}
          className="w-full touch-none rounded-md"
          data-testid={`${testid}-canvas`}
          onMouseDown={start}
          onMouseMove={move}
          onMouseUp={end}
          onMouseLeave={end}
          onTouchStart={start}
          onTouchMove={move}
          onTouchEnd={end}
        />
        {!hasImage && (
          <span className="pointer-events-none absolute inset-0 flex items-center justify-center text-xs text-slate-400">
            Tanda tangan di sini
          </span>
        )}
      </div>
      <Button type="button" variant="ghost" size="sm" onClick={clear}
        data-testid={`${testid}-clear`} className="mt-1 h-7 text-xs text-muted-foreground">
        <Eraser size={14} className="mr-1" /> Hapus
      </Button>
    </div>
  );
}
