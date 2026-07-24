"use client"
import { useState } from "react"
import type { Requirement, Framework } from "@/lib/types"
import { FrameworkBadge, TierBadge } from "./ui"

const TABS: { key: Framework | "All"; label: string }[] = [
  { key: "All", label: "All" },
  { key: "REAMS", label: "REAMS" },
  { key: "EUAIAct", label: "EU AI Act" },
  { key: "HorizonEurope", label: "Horizon" },
  { key: "ACMConference", label: "ACM" },
]

export default function RequirementsTable({ requirements }: { requirements: Requirement[] }) {
  const [tab, setTab] = useState<Framework | "All">("All")
  if (!requirements?.length) {
    return <p className="text-[11px] text-stone-400">No requirements cited.</p>
  }
  const rows = tab === "All" ? requirements : requirements.filter((r) => r.framework === tab)

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="mb-1.5 flex shrink-0 flex-wrap gap-1" role="tablist" aria-label="Framework filter">
        {TABS.map((t) => (
          <button
            key={t.key}
            role="tab"
            aria-selected={tab === t.key}
            onClick={() => setTab(t.key)}
            className={`rounded border px-2 py-0.5 text-[10px] font-semibold ${
              tab === t.key
                ? "border-pine-700 bg-pine-700 text-white"
                : "border-stone-300 bg-white text-stone-600 hover:border-pine-600"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="report-panel min-h-0 flex-1 rounded border-2 border-stone-200">
        <table className="w-full text-[11px]">
          <thead className="sticky top-0 bg-stone-50 text-left text-[9px] uppercase tracking-wide text-stone-500">
            <tr>
              <th className="px-2 py-1.5">ID</th>
              <th className="px-2 py-1.5">Requirement</th>
              <th className="px-2 py-1.5">Fw</th>
              <th className="px-2 py-1.5">Tier</th>
              <th className="px-2 py-1.5">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-stone-100">
            {rows.map((r, i) => (
              <tr key={i} className="align-top">
                <td className="whitespace-nowrap px-2 py-1.5 font-mono text-[10px] text-pine-700">{r.requirement_id}</td>
                <td className="px-2 py-1.5 leading-snug text-stone-700">{r.requirement_text}</td>
                <td className="px-2 py-1.5"><FrameworkBadge framework={r.framework} /></td>
                <td className="px-2 py-1.5"><TierBadge tier={r.tier} /></td>
                <td className="px-2 py-1.5 leading-snug text-stone-600">{r.action_needed}</td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={5} className="px-2 py-3 text-center text-stone-400">
                  No requirements cited for this framework.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
