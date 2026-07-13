"use client"
import { useState } from "react"
import { SectionTitle, Card } from "./ui"

export default function Checklist({ title, items }: { title: string; items: string[] }) {
  const [checked, setChecked] = useState<boolean[]>(() => items.map(() => false))
  if (!items?.length) return null
  return (
    <section>
      <SectionTitle>{title}</SectionTitle>
      <Card>
        <ul className="space-y-2">
          {items.map((item, i) => (
            <li key={i}>
              <label className="flex gap-2.5 items-start text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={checked[i]}
                  onChange={() => setChecked((c) => c.map((v, j) => (j === i ? !v : v)))}
                  className="mt-0.5 accent-[#25573f]"
                />
                <span className={checked[i] ? "line-through text-stone-400" : "text-stone-700"}>{item}</span>
              </label>
            </li>
          ))}
        </ul>
      </Card>
    </section>
  )
}
