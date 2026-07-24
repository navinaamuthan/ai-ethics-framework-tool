"use client"
import { useState } from "react"
import type { Risk } from "@/lib/types"
import { riskStyles } from "./ui"

export default function RiskCards({ risks }: { risks: Risk[] }) {
  const [open, setOpen] = useState<number | null>(0)
  if (!risks?.length) {
    return <p className="text-[11px] text-stone-400">No risks identified.</p>
  }
  return (
    <div className="space-y-1.5">
      {risks.map((r, i) => {
        const s = riskStyles[r.severity] ?? riskStyles.Medium
        const isOpen = open === i
        return (
          <div
            key={i}
            className={`overflow-hidden rounded border-2 ${s.border} ${isOpen ? s.soft : "border-stone-200 bg-white"}`}
          >
            <button
              onClick={() => setOpen(isOpen ? null : i)}
              className="flex w-full items-center gap-2 px-2.5 py-1.5 text-left"
              aria-expanded={isOpen}
            >
              <span className={`h-2 w-2 shrink-0 rounded-sm ${s.dot}`} />
              <span className="flex-1 text-[12px] font-medium leading-snug text-stone-800">{r.risk}</span>
              <span className={`shrink-0 text-[10px] font-bold uppercase tracking-wide ${s.text}`}>{r.severity}</span>
              <span className="w-3 shrink-0 text-center text-[11px] text-stone-400">{isOpen ? "−" : "+"}</span>
            </button>
            {isOpen && <p className="border-t border-stone-200/80 px-2.5 py-1.5 text-[11px] leading-snug text-stone-600">{r.explanation}</p>}
          </div>
        )
      })}
    </div>
  )
}
