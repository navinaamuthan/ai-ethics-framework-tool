import type { Framework } from "@/lib/types"

export const riskStyles: Record<string, { bg: string; text: string; border: string; dot: string; soft: string }> = {
  High: {
    bg: "bg-red-600",
    text: "text-red-700",
    border: "border-red-600",
    dot: "bg-red-600",
    soft: "bg-red-50 border-red-200",
  },
  Medium: {
    bg: "bg-amber-600",
    text: "text-amber-700",
    border: "border-amber-600",
    dot: "bg-amber-600",
    soft: "bg-amber-50 border-amber-200",
  },
  Low: {
    bg: "bg-green-600",
    text: "text-green-700",
    border: "border-green-600",
    dot: "bg-green-600",
    soft: "bg-green-50 border-green-200",
  },
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
    <span className={`inline-block rounded border px-1.5 py-0.5 text-[10px] font-semibold leading-none ${s.badge}`}>
      {s.label}
    </span>
  )
}

export function TierBadge({ tier }: { tier: string }) {
  const isT1 = tier.includes("Tier 1")
  return (
    <span
      className={`inline-block rounded px-1.5 py-0.5 text-[10px] font-semibold leading-none ${
        isT1 ? "bg-pine-700 text-white" : "border border-pine-700 text-pine-700"
      }`}
    >
      {isT1 ? "T1" : "T2"}
    </span>
  )
}

export function SectionTitle({
  children,
  count,
  className = "",
}: {
  children: React.ReactNode
  count?: number
  className?: string
}) {
  return (
    <div className={`mb-2 flex items-baseline justify-between gap-2 ${className}`}>
      <h2 className="font-display text-[13px] font-semibold uppercase tracking-[0.08em] text-pine-800">
        {children}
      </h2>
      {typeof count === "number" && (
        <span className="rounded bg-pine-100 px-1.5 py-0.5 font-mono text-[10px] font-medium text-pine-800">
          {count}
        </span>
      )}
    </div>
  )
}

export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-md border-2 border-stone-200 bg-white shadow-[3px_3px_0_0_rgba(29,70,52,0.08)] ${className}`}>
      {children}
    </div>
  )
}

export function Panel({
  children,
  className = "",
  title,
  count,
  accent = "border-l-pine-700",
  scroll = true,
}: {
  children: React.ReactNode
  className?: string
  title?: string
  count?: number
  accent?: string
  scroll?: boolean
}) {
  return (
    <section
      className={`flex min-h-0 flex-col rounded-md border-2 border-stone-200 border-l-[5px] bg-white ${accent} ${className}`}
    >
      {title && (
        <div className="shrink-0 border-b border-stone-100 px-3 py-2">
          <SectionTitle count={count} className="mb-0">
            {title}
          </SectionTitle>
        </div>
      )}
      <div className={`flex-1 px-3 py-2 ${scroll ? "report-panel" : "min-h-0 overflow-hidden"}`}>{children}</div>
    </section>
  )
}
