"use client"
import { useState } from "react"
import type { Requirement, Framework } from "@/lib/types"
import { FrameworkBadge, TierBadge, SectionTitle } from "./ui"

const TABS: { key: Framework | "All"; label: string }[] = [
  { key: "All", label: "All" },
  { key: "REAMS", label: "REAMS" },
  { key: "EUAIAct", label: "EU AI Act" },
  { key: "HorizonEurope", label: "Horizon Europe" },
  { key: "ACMConference", label: "ACM/NeurIPS" },
]

export default function RequirementsTable({ requirements }: { requirements: Requirement[] }) {
  const [tab, setTab] = useState<Framework | "All">("All")
  if (!requirements?.length) return null
  const rows = tab === "All" ? requirements : requirements.filter((r) => r.framework === tab)

  return (
    <section>
      <SectionTitle>Applicable requirements</SectionTitle>
      <div className="flex flex-wrap gap-1 mb-3" role="tablist" aria-label="Framework filter">
        {TABS.map((t) => (
          <button
            key={t.key}
            role="tab"
            aria-selected={tab === t.key}
            onClick={() => setTab(t.key)}
            className={`rounded-full px-3 py-1 text-xs font-medium border ${
              tab === t.key
                ? "bg-pine-700 text-white border-pine-700"
                : "bg-white text-stone-600 border-stone-300 hover:border-pine-600"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="overflow-x-auto rounded-lg border border-stone-200">
        <table className="w-full text-sm">
          <thead className="bg-stone-50 text-left text-xs uppercase tracking-wide text-stone-500">
            <tr>
              <th className="px-3 py-2">ID</th>
              <th className="px-3 py-2">Requirement</th>
              <th className="px-3 py-2">Framework</th>
              <th className="px-3 py-2">Tier</th>
              <th className="px-3 py-2">Action needed</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-stone-100">
            {rows.map((r, i) => (
              <tr key={i} className="align-top">
                <td className="px-3 py-2 font-mono text-xs text-pine-700 whitespace-nowrap">{r.requirement_id}</td>
                <td className="px-3 py-2 text-stone-700">{r.requirement_text}</td>
                <td className="px-3 py-2"><FrameworkBadge framework={r.framework} /></td>
                <td className="px-3 py-2"><TierBadge tier={r.tier} /></td>
                <td className="px-3 py-2 text-stone-600">{r.action_needed}</td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td colSpan={5} className="px-3 py-4 text-center text-stone-400 text-sm">No requirements cited for this framework.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}
