export default function RiskSummary({ summary }: { summary: string }) {
  return (
    <p className="text-[15px] leading-relaxed text-stone-700 border-l-4 border-pine-600 pl-4">
      {summary}
    </p>
  )
}
