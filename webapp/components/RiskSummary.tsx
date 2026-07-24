export default function RiskSummary({ summary }: { summary: string }) {
  return (
    <p className="line-clamp-3 border-l-[4px] border-pine-600 bg-pine-50/60 py-1.5 pl-3 pr-2 text-[12px] leading-snug text-stone-700">
      {summary}
    </p>
  )
}
