"use client"
import { useState } from "react"
import type { RetrievalMetadata } from "@/lib/types"

export default function RetrievalPanel({ meta }: { meta: RetrievalMetadata }) {
  const [open, setOpen] = useState(true)
  const cited = new Set(meta.requirements_cited)
  const notCited = meta.requirements_retrieved_ids.filter((id) => !cited.has(id))

  return (
    <section className="rounded-lg border border-pine-600/30 bg-pine-50">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-3 text-left"
        aria-expanded={open}
      >
        <span className="font-display font-semibold text-pine-800">Retrieval transparency</span>
        <span className="text-pine-700 text-sm">{open ? "Hide" : "Show"}</span>
      </button>
      {open && (
        <div className="px-5 pb-5 space-y-4 text-sm">
          <p className="text-stone-600">
            Retrieved from the knowledge graph: <strong>{meta.requirements_retrieved}</strong> requirements,{" "}
            <strong>{meta.incidents_retrieved}</strong> incidents, <strong>{meta.rights_matched}</strong> Charter
            rights. The model cited <strong>{meta.requirements_cited.length}</strong> of the retrieved requirements —
            the pills below make the retrieval/generation gap visible.
          </p>
          <div>
            <div className="text-xs uppercase tracking-wide text-stone-500 mb-1.5">
              Cited by the model ({meta.requirements_cited.length})
            </div>
            <div className="flex flex-wrap gap-1.5">
              {meta.requirements_cited.map((id) => (
                <span key={id} className="rounded-full bg-pine-700 text-white font-mono text-xs px-2.5 py-1">{id}</span>
              ))}
              {meta.requirements_cited.length === 0 && <span className="text-stone-400 text-xs">None</span>}
            </div>
          </div>
          <div>
            <div className="text-xs uppercase tracking-wide text-stone-500 mb-1.5">
              Retrieved but not cited ({notCited.length})
            </div>
            <div className="flex flex-wrap gap-1.5">
              {notCited.map((id) => (
                <span key={id} className="rounded-full bg-stone-200 text-stone-600 font-mono text-xs px-2.5 py-1">{id}</span>
              ))}
              {notCited.length === 0 && <span className="text-stone-400 text-xs">None — full coverage</span>}
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
