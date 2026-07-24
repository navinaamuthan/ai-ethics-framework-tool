import type { Incident } from "@/lib/types"

export default function Incidents({ incidents }: { incidents: Incident[] }) {
  if (!incidents?.length) {
    return <p className="text-[11px] text-stone-400">No historical precedents cited.</p>
  }
  return (
    <div className="space-y-1.5">
      {incidents.map((inc, i) => (
        <div key={i} className="rounded border-2 border-stone-200 bg-white p-2">
          <div className="font-mono text-[9px] text-stone-400">{inc.incident_id}</div>
          <div className="text-[11px] font-semibold leading-snug text-stone-800">{inc.incident_title}</div>
          <p className="mt-0.5 line-clamp-2 text-[10px] leading-snug text-stone-600">
            <span className="font-semibold text-pine-700">Lesson:</span> {inc.lesson}
          </p>
        </div>
      ))}
    </div>
  )
}
