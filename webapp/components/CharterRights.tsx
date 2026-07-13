import type { CharterRight } from "@/lib/types"
import { SectionTitle, Card } from "./ui"

export default function CharterRights({ rights }: { rights: CharterRight[] }) {
  if (!rights?.length) return null
  return (
    <section>
      <SectionTitle>EU Charter rights at risk</SectionTitle>
      <div className="space-y-2">
        {rights.map((r, i) => (
          <Card key={i} className="flex gap-3 items-start">
            <div className="shrink-0 rounded-md bg-pine-100 text-pine-800 font-display font-bold px-2.5 py-1.5 text-sm">
              {r.article.replace("Article", "Art.")}
            </div>
            <div>
              <div className="font-medium text-sm">{r.right_name}</div>
              <p className="text-xs text-stone-600 mt-0.5">{r.relevance}</p>
            </div>
          </Card>
        ))}
      </div>
    </section>
  )
}
