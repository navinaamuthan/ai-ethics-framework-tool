"use client"
import { useState } from "react"
import type { Risk } from "@/lib/types"
import { riskStyles, SectionTitle, Card } from "./ui"

export default function RiskCards({ risks }: { risks: Risk[] }) {
  const [open, setOpen] = useState<number | null>(0)
  if (!risks?.length) return null
  return (
    <section>
      <SectionTitle>Identified risks</SectionTitle>
      <div className="space-y-2">
        {risks.map((r, i) => {
          const s = riskStyles[r.severity] ?? riskStyles.Medium
          const isOpen = open === i
          return (
            <Card key={i} className="p-0 overflow-hidden">
              <button
                onClick={() => setOpen(isOpen ? null : i)}
                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-stone-50"
                aria-expanded={isOpen}
              >
                <span className={`h-2.5 w-2.5 rounded-full shrink-0 ${s.dot}`} />
                <span className="font-medium text-sm flex-1">{r.risk}</span>
                <span className={`text-xs font-semibold ${s.text}`}>{r.severity}</span>
                <span className="text-stone-400 text-xs">{isOpen ? "−" : "+"}</span>
              </button>
              {isOpen && <p className="px-4 pb-4 text-sm text-stone-600">{r.explanation}</p>}
            </Card>
          )
        })}
      </div>
    </section>
  )
}
