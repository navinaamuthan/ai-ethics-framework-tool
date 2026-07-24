"use client"
import type { Finding } from "@/lib/dimension-rules"

export default function DimensionProfile({ findings }: { findings: Finding[] }) {
  if (!findings.length) {
    return (
      <p className="text-[11px] leading-snug text-stone-500">
        No risk-dimension flags. All deterministic rules pass.
      </p>
    )
  }

  const byDim = findings.reduce<Record<string, Finding[]>>((acc, f) => {
    ;(acc[f.dimension] ??= []).push(f)
    return acc
  }, {})

  return (
    <div className="space-y-2">
      {Object.entries(byDim).map(([dim, items]) => (
        <div key={dim}>
          <h4 className="mb-1 text-[10px] font-bold uppercase tracking-wide text-pine-800">{dim}</h4>
          <ul className="space-y-1">
            {items.map((f) => (
              <li
                key={f.rule}
                className={`rounded border px-2 py-1 text-[11px] leading-snug ${
                  f.severity === "violation"
                    ? "border-red-200 bg-red-50 text-red-900"
                    : "border-amber-200 bg-amber-50 text-amber-900"
                }`}
              >
                <span className="mr-1.5 font-mono text-[10px]">P{f.priority}</span>
                <span className="mr-1.5 text-[9px] font-semibold uppercase tracking-wide">{f.severity}</span>
                {f.rule}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}
