import React from "react";
import { JUDGMENTS } from "@/lib/meta";

export default function JudgmentToggle({ value, onChange, testid }) {
  return (
    <div className="grid grid-cols-4 gap-1.5" data-testid={testid}>
      {JUDGMENTS.map((j) => {
        const active = value === j.key;
        return (
          <button
            key={j.key}
            type="button"
            data-testid={`${testid}-${j.key}`}
            onClick={() => onChange(active ? null : j.key)}
            className={`flex flex-col items-center justify-center rounded-md border py-2 min-h-[48px] transition-colors ${
              active
                ? `${j.bg} text-white border-transparent shadow-sm`
                : "bg-white border-border text-slate-500 hover:border-slate-300"
            }`}
          >
            <span className="text-base leading-none font-bold">{j.mark}</span>
            <span className="text-[10px] mt-1 leading-tight text-center px-0.5">{j.label}</span>
          </button>
        );
      })}
    </div>
  );
}
