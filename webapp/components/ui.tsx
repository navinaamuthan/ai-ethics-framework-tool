import type { Framework } from "@/lib/types"

export const riskStyles: Record<string, { bg: string; text: string; border: string; dot: string }> = {
  High: { bg: "bg-red-600", text: "text-red-700", border: "border-red-600", dot: "bg-red-600" },
  Medium: { bg: "bg-amber-600", text: "text-amber-700", border: "border-amber-600", dot: "bg-amber-600" },
  Low: { bg: "bg-green-600", text: "text-green-700", border: "border-green-600", dot: "bg-green-600" },
}

export const frameworkStyles: Record<Framework, { badge: string; label: string }> = {
  REAMS: { badge: "bg-blue-100 text-blue-800 border-blue-300", label: "REAMS" },
  EUAIAct: { badge: "bg-purple-100 text-purple-800 border-purple-300", label: "EU AI Act" },
  HorizonEurope: { badge: "bg-teal-100 text-teal-800 border-teal-300", label: "Horizon Europe" },
  ACMConference: { badge: "bg-orange-100 text-orange-800 border-orange-300", label: "ACM/NeurIPS" },
}

export function FrameworkBadge({ framework }: { framework: Framework }) {
  const s = frameworkStyles[framework] ?? { badge: "bg-stone-100 text-stone-700 border-stone-300", label: framework }
  return (
    <span className={`inline-block rounded-full border px-2 py-0.5 text-xs font-medium ${s.badge}`}>
      {s.label}
    </span>
  )
}

export function TierBadge({ tier }: { tier: string }) {
  const isT1 = tier.includes("Tier 1")
  return (
    <span
      className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${
        isT1 ? "bg-pine-700 text-white" : "border border-pine-700 text-pine-700"
      }`}
    >
      {isT1 ? "Tier 1 Mandatory" : "Tier 2 Reflective"}
    </span>
  )
}

export function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h2 className="font-display text-xl font-semibold text-pine-800 mb-3">{children}</h2>
}

export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`rounded-lg border border-stone-200 bg-white p-4 ${className}`}>{children}</div>
}
