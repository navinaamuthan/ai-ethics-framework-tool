import { riskStyles } from "./ui"

export default function RiskBanner({
  level,
  confidence,
  reamsLikely,
}: {
  level: "High" | "Medium" | "Low"
  confidence: "HIGH" | "LOW"
  reamsLikely: boolean
}) {
  const s = riskStyles[level] ?? riskStyles.Medium
  return (
    <div
      className={`${s.bg} flex shrink-0 items-center gap-4 rounded-md border-2 border-black/10 px-4 py-2.5 text-white shadow-[4px_4px_0_0_rgba(0,0,0,0.12)]`}
    >
      <div className="flex items-baseline gap-3">
        <span className="text-[10px] font-semibold uppercase tracking-[0.14em] opacity-80">Risk</span>
        <span className="font-display text-2xl font-bold leading-none tracking-tight">{level.toUpperCase()}</span>
      </div>
      <div className="ml-auto flex flex-wrap items-center gap-1.5 text-[11px]">
        <span className="rounded border border-white/25 bg-white/15 px-2.5 py-1 font-medium">
          Confidence <strong className="ml-1">{confidence}</strong>
        </span>
        <span className="rounded border border-white/25 bg-white/15 px-2.5 py-1 font-medium">
          REAMS likely <strong className="ml-1">{reamsLikely ? "Yes" : "No"}</strong>
        </span>
      </div>
    </div>
  )
}
