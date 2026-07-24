"use client"
import { useState } from "react"

export default function Checklist({ title, items }: { title: string; items: string[] }) {
  const [checked, setChecked] = useState<boolean[]>(() => items.map(() => false))
  if (!items?.length) return null
  const done = checked.filter(Boolean).length

  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between gap-2">
        <h3 className="text-[10px] font-bold uppercase tracking-wide text-pine-800">{title}</h3>
        <span className="font-mono text-[10px] text-stone-400">
          {done}/{items.length}
        </span>
      </div>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i}>
            <label className="flex cursor-pointer items-start gap-2 text-[11px] leading-snug">
              <input
                type="checkbox"
                checked={checked[i]}
                onChange={() => setChecked((c) => c.map((v, j) => (j === i ? !v : v)))}
                className="mt-0.5 accent-[#25573f]"
              />
              <span className={checked[i] ? "text-stone-400 line-through" : "text-stone-700"}>{item}</span>
            </label>
          </li>
        ))}
      </ul>
    </div>
  )
}
