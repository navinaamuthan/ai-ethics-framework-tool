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
    <div className={`${s.bg} rounded-lg px-6 py-5 text-white flex flex-col sm:flex-row sm:items-center gap-3`}>
      <div>
        <div className="text-xs uppercase tracking-widest opacity-80">Overall risk level</div>
        <div className="font-display text-4xl font-bold">{level.toUpperCase()}</div>
      </div>
      <div className="sm:ml-auto flex flex-wrap gap-2 text-sm">
        <span className="rounded-full bg-white/20 px-3 py-1">
          Confidence: <strong>{confidence}</strong>
        </span>
        <span className="rounded-full bg-white/20 px-3 py-1">
          REAMS clearance likely: <strong>{reamsLikely ? "Yes" : "No"}</strong>
        </span>
      </div>
    </div>
  )
}
