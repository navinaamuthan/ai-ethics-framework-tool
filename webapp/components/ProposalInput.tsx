"use client"
import { useState } from "react"

const MODELS = [
  { id: "llama-3.3-70b-versatile", label: "Llama 3.3 70B (recommended)" },
  { id: "qwen/qwen3-32b", label: "Qwen3 32B" },
  { id: "llama-3.1-8b-instant", label: "Llama 3.1 8B" },
]

export default function ProposalInput({
  onSubmit,
  disabled,
}: {
  onSubmit: (text: string, model: string) => void
  disabled: boolean
}) {
  const [text, setText] = useState("")
  const [model, setModel] = useState(MODELS[0].id)
  const tooShort = text.trim().length < 50

  return (
    <div className="w-full max-w-3xl mx-auto">
      <label htmlFor="proposal" className="block text-sm font-medium text-stone-600 mb-2">
        Paste your AI research proposal
      </label>
      <textarea
        id="proposal"
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={10}
        placeholder="Describe the research aims, the AI system, the data involved, and the affected people or groups…"
        className="w-full rounded-lg border border-stone-300 p-4 text-sm focus:outline-none focus:ring-2 focus:ring-pine-600 resize-y"
      />
      <div className="mt-3 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        <div className="flex items-center gap-2">
          <label htmlFor="model" className="text-sm text-stone-600">Model</label>
          <select
            id="model"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="rounded-md border border-stone-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-pine-600"
          >
            {MODELS.map((m) => (
              <option key={m.id} value={m.id}>{m.label}</option>
            ))}
          </select>
        </div>
        <button
          onClick={() => onSubmit(text, model)}
          disabled={disabled || tooShort}
          className="sm:ml-auto rounded-lg bg-pine-700 px-6 py-2.5 text-sm font-medium text-white hover:bg-pine-800 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Run ethics assessment
        </button>
      </div>
      {tooShort && text.length > 0 && (
        <p className="mt-2 text-xs text-stone-500">Enter at least 50 characters.</p>
      )}
    </div>
  )
}
