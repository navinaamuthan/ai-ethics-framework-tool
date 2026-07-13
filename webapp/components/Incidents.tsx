import type { Incident } from "@/lib/types"
import { SectionTitle, Card } from "./ui"

export default function Incidents({ incidents }: { incidents: Incident[] }) {
  if (!incidents?.length) return null
  return (
    <section>
      <SectionTitle>Historical precedents</SectionTitle>
      <div className="space-y-2">
        {incidents.map((inc, i) => (
          <Card key={i}>
            <div className="font-mono text-xs text-stone-400">{inc.incident_id}</div>
            <div className="font-medium text-sm mt-0.5">{inc.incident_title}</div>
            <p className="text-xs text-stone-600 mt-1"><span className="font-medium text-pine-700">Lesson:</span> {inc.lesson}</p>
          </Card>
        ))}
      </div>
    </section>
  )
}
