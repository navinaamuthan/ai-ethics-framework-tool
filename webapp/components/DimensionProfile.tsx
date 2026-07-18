"use client"
import type { Finding } from "@/lib/dimension-rules"

export default function DimensionProfile({ findings }: { findings: Finding[] }) {
  if (!findings.length) {
    return (
      <section className="rounded-lg border border-stone-200 bg-stone-50 px-5 py-4">
        <h3 className="font-display text-lg font-semibold text-stone-800 mb-1">
          Deterministic risk dimensions
        </h3>
        <p className="text-sm text-stone-500 mb-2">
          Deterministic rule verdicts — computed without the LLM; rules and priorities are public data
          in the repository.
        </p>
        <p className="text-sm text-stone-600">No risk-dimension flags. All scrutable rules pass.</p>
      </section>
    )
  }

  const byDim = findings.reduce<Record<string, Finding[]>>((acc, f) => {
    ;(acc[f.dimension] ??= []).push(f)
    return acc
  }, {})

  return (
    <section className="rounded-lg border border-stone-200 bg-stone-50 px-5 py-4 space-y-3">
      <div>
        <h3 className="font-display text-lg font-semibold text-stone-800 mb-1">
          Deterministic risk dimensions
        </h3>
        <p className="text-sm text-stone-500">
          Deterministic rule verdicts — computed without the LLM; rules and priorities are public data
          in the repository.
        </p>
      </div>
      {Object.entries(byDim).map(([dim, items]) => (
        <div key={dim}>
          <h4 className="text-sm font-semibold text-pine-800 mb-1">{dim}</h4>
          <ul className="space-y-1">
            {items.map((f) => (
              <li
                key={f.rule}
                className={`text-sm px-3 py-2 rounded border ${
                  f.severity === "violation"
                    ? "border-red-200 bg-red-50 text-red-900"
                    : "border-amber-200 bg-amber-50 text-amber-900"
                }`}
              >
                <span className="font-mono text-xs mr-2">P{f.priority}</span>
                <span className="uppercase text-xs mr-2 tracking-wide">{f.severity}</span>
                {f.rule}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  )
}
