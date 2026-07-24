import type { Mitigation } from "@/lib/types"
import { riskStyles } from "./ui"

export default function Mitigations({ mitigations }: { mitigations: Mitigation[] }) {
  if (!mitigations?.length) {
    return <p className="text-[11px] text-stone-400">No mitigations recommended.</p>
  }
  return (
    <ul className="space-y-1.5">
      {mitigations.map((m, i) => {
        const s = riskStyles[m.priority] ?? riskStyles.Medium
        return (
          <li key={i} className="flex items-start gap-2 text-[11px] leading-snug">
            <span className={`mt-1 h-2 w-2 shrink-0 rounded-sm ${s.dot}`} title={`${m.priority} priority`} />
            <span className="text-stone-700">{m.mitigation}</span>
          </li>
        )
      })}
    </ul>
  )
}
