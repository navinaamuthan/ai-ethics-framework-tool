"use client"
import { useState } from "react"

const MODELS = [
  { id: "llama-3.3-70b-versatile", label: "Llama 3.3 70B (recommended)" },
  { id: "qwen/qwen3-32b", label: "Qwen3 32B" },
  { id: "llama-3.1-8b-instant", label: "Llama 3.1 8B" },
]

/** Optum-style health risk stratification case (evaluation P01). */
export const SAMPLE_PROPOSAL = `This research proposes to develop a commercial health risk stratification algorithm to identify high-need patients for enrolment in care management programmes across a network of US hospital systems. The algorithm will use insurance claims data as a proxy for health need, predicting which patients require additional clinical resources based on historical healthcare costs, prior diagnoses, medication use, and utilisation patterns from electronic health records covering approximately 200 million patients annually. Patients scoring in the top 3 percentile will automatically be referred to care management; those in the top 45 percentile will be assessed for referral. The algorithm will not explicitly use race as a predictive variable. However, because Black patients have historically incurred lower healthcare costs than white patients with equivalent chronic disease burden — due to structural barriers to healthcare access including cost, discrimination, and geographic distance — the cost proxy will systematically underestimate the health needs of Black patients. The algorithm has not undergone independent bias auditing prior to deployment. No mechanism for algorithmic review or patient appeal of care management non-referral decisions is planned.`

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
  const chars = text.trim().length

  function runSample() {
    if (disabled) return
    setText(SAMPLE_PROPOSAL)
    onSubmit(SAMPLE_PROPOSAL, model)
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="rounded-xl border-[3px] border-pine-900/20 bg-white/90 p-5 shadow-[8px_8px_0_0_rgba(20,49,36,0.18)] backdrop-blur-sm sm:p-6">
        <div className="mb-3 flex items-end justify-between gap-3">
          <label htmlFor="proposal" className="block text-sm font-semibold text-pine-900">
            Paste your AI research proposal
          </label>
          <span className={`font-mono text-[11px] ${chars >= 50 ? "text-pine-700" : "text-stone-400"}`}>
            {chars}/50
          </span>
        </div>
        <textarea
          id="proposal"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key !== "Tab" || disabled) return
            // Empty field: Tab loads sample and runs assessment
            if (text.trim().length === 0) {
              e.preventDefault()
              runSample()
            }
          }}
          rows={8}
          placeholder="Describe the research aims, the AI system, the data involved, and the affected people or groups… (or press Tab for a sample)"
          className="w-full resize-none rounded-lg border-2 border-stone-200 bg-stone-50/80 p-4 text-sm leading-relaxed text-stone-800 placeholder:text-stone-400 focus:border-pine-600 focus:bg-white focus:outline-none focus:ring-0"
        />
        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="flex flex-wrap items-center gap-2">
            <label htmlFor="model" className="text-xs font-medium uppercase tracking-wide text-stone-500">
              Model
            </label>
            <select
              id="model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="rounded-md border-2 border-stone-200 bg-white px-2.5 py-2 text-sm text-stone-700 focus:border-pine-600 focus:outline-none"
            >
              {MODELS.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={runSample}
              disabled={disabled}
              className="rounded-md border-2 border-pine-800/20 bg-pine-50 px-2.5 py-1.5 text-[11px] font-semibold text-pine-800 transition hover:border-pine-700 hover:bg-pine-100 disabled:opacity-40"
              title="Load sample health-risk proposal and run assessment (or press Tab in an empty box)"
            >
              Try sample
            </button>
          </div>
          <button
            onClick={() => onSubmit(text, model)}
            disabled={disabled || tooShort}
            className="sm:ml-auto rounded-lg border-2 border-pine-900 bg-pine-700 px-6 py-2.5 text-sm font-semibold text-white shadow-[3px_3px_0_0_#143124] transition hover:translate-x-px hover:translate-y-px hover:bg-pine-800 hover:shadow-[2px_2px_0_0_#143124] disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none disabled:hover:translate-x-0 disabled:hover:translate-y-0"
          >
            Run ethics assessment
          </button>
        </div>
        {text.length === 0 && (
          <p className="mt-2 text-xs text-stone-500">
            Press <kbd className="rounded border border-stone-300 bg-stone-100 px-1 font-mono text-[10px]">Tab</kbd>{" "}
            in the empty box to load a sample proposal and run — or click Try sample.
          </p>
        )}
        {tooShort && text.length > 0 && (
          <p className="mt-2 text-xs text-stone-500">Enter at least 50 characters to run an assessment.</p>
        )}
      </div>
    </div>
  )
}
