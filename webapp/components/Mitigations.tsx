import type { Mitigation } from "@/lib/types"
import { riskStyles, SectionTitle, Card } from "./ui"

export default function Mitigations({ mitigations }: { mitigations: Mitigation[] }) {
  if (!mitigations?.length) return null
  return (
    <section>
      <SectionTitle>Recommended mitigations</SectionTitle>
      <Card>
        <ul className="space-y-2">
          {mitigations.map((m, i) => {
            const s = riskStyles[m.priority] ?? riskStyles.Medium
            return (
              <li key={i} className="flex gap-2 text-sm items-start">
                <span className={`mt-1.5 h-2 w-2 rounded-full shrink-0 ${s.dot}`} title={`${m.priority} priority`} />
                <span className="text-stone-700">{m.mitigation}</span>
              </li>
            )
          })}
        </ul>
      </Card>
    </section>
  )
}
