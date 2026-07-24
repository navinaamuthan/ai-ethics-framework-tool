"use client"
import { useState } from "react"
import type { RetrievalMetadata } from "@/lib/types"

export default function RetrievalPanel({ meta }: { meta: RetrievalMetadata }) {
  const [open, setOpen] = useState(false)
  const cited = new Set(meta.requirements_cited)
  const notCited = meta.requirements_retrieved_ids.filter((id) => !cited.has(id))

  return (
    <section className="shrink-0 rounded-md border-2 border-pine-700/25 bg-pine-50">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-3 px-3 py-1.5 text-left"
        aria-expanded={open}
      >
        <span className="font-display text-[12px] font-semibold text-pine-800">Retrieval transparency</span>
        <span className="font-mono text-[10px] text-pine-700/80">
          {meta.requirements_retrieved} req · {meta.incidents_retrieved} inc · {meta.rights_matched} rights ·{" "}
          {meta.requirements_cited.length} cited
        </span>
        <span className="ml-auto text-[10px] font-semibold uppercase tracking-wide text-pine-700">
          {open ? "Hide" : "Show"}
        </span>
      </button>
      {open && (
        <div className="max-h-28 space-y-2 overflow-y-auto border-t border-pine-700/15 px-3 py-2 text-[11px]">
          <p className="leading-snug text-stone-600">
            Retrieved <strong>{meta.requirements_retrieved}</strong> requirements,{" "}
            <strong>{meta.incidents_retrieved}</strong> incidents, <strong>{meta.rights_matched}</strong> Charter
            rights. Model cited <strong>{meta.requirements_cited.length}</strong> — pills show the retrieval/generation gap.
          </p>
          <div>
            <div className="mb-1 text-[9px] font-semibold uppercase tracking-wide text-stone-500">
              Cited ({meta.requirements_cited.length})
            </div>
            <div className="flex flex-wrap gap-1">
              {meta.requirements_cited.map((id) => (
                <span key={id} className="rounded bg-pine-700 px-1.5 py-0.5 font-mono text-[9px] text-white">
                  {id}
                </span>
              ))}
              {meta.requirements_cited.length === 0 && <span className="text-[10px] text-stone-400">None</span>}
            </div>
          </div>
          <div>
            <div className="mb-1 text-[9px] font-semibold uppercase tracking-wide text-stone-500">
              Retrieved not cited ({notCited.length})
            </div>
            <div className="flex flex-wrap gap-1">
              {notCited.slice(0, 40).map((id) => (
                <span key={id} className="rounded bg-stone-200 px-1.5 py-0.5 font-mono text-[9px] text-stone-600">
                  {id}
                </span>
              ))}
              {notCited.length > 40 && (
                <span className="text-[10px] text-stone-400">+{notCited.length - 40} more</span>
              )}
              {notCited.length === 0 && <span className="text-[10px] text-stone-400">None — full coverage</span>}
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
