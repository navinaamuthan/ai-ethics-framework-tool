import type { CharterRight } from "@/lib/types"

export default function CharterRights({ rights }: { rights: CharterRight[] }) {
  if (!rights?.length) {
    return <p className="text-[11px] text-stone-400">No Charter rights flagged.</p>
  }
  return (
    <div className="space-y-1.5">
      {rights.map((r, i) => (
        <div key={i} className="flex gap-2 rounded border-2 border-stone-200 bg-stone-50/80 p-2">
          <div className="shrink-0 rounded bg-pine-700 px-1.5 py-1 font-display text-[10px] font-bold leading-none text-white">
            {r.article.replace("Article", "Art.")}
          </div>
          <div className="min-w-0">
            <div className="text-[11px] font-semibold text-stone-800">{r.right_name}</div>
            <p className="mt-0.5 line-clamp-2 text-[10px] leading-snug text-stone-600">{r.relevance}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
