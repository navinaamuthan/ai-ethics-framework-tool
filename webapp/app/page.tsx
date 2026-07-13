"use client"
import { useEffect, useState } from "react"
import type { AssessmentResponse } from "@/lib/types"
import ProposalInput from "@/components/ProposalInput"
import RiskBanner from "@/components/RiskBanner"
import RiskSummary from "@/components/RiskSummary"
import RiskCards from "@/components/RiskCards"
import RequirementsTable from "@/components/RequirementsTable"
import CharterRights from "@/components/CharterRights"
import Incidents from "@/components/Incidents"
import Mitigations from "@/components/Mitigations"
import Checklist from "@/components/Checklist"
import RetrievalPanel from "@/components/RetrievalPanel"
import KGMetadata from "@/components/KGMetadata"

const STEPS = ["Extracting keywords", "Querying knowledge graph", "Generating assessment"]

export default function Home() {
  const [state, setState] = useState<"idle" | "loading" | "results">("idle")
  const [step, setStep] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AssessmentResponse | null>(null)

  useEffect(() => {
    if (state !== "loading") return
    setStep(0)
    const t1 = setTimeout(() => setStep(1), 900)
    const t2 = setTimeout(() => setStep(2), 2200)
    return () => { clearTimeout(t1); clearTimeout(t2) }
  }, [state])

  async function assess(proposalText: string, model: string) {
    setError(null)
    setState("loading")
    try {
      const res = await fetch("/api/assess", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ proposalText, model }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error + (data.detail ? ` — ${data.detail}` : ""))
      setResult(data)
      setState("results")
    } catch (e) {
      setError(String(e))
      setState("idle")
    }
  }

  return (
    <main className="min-h-screen">
      <header className="border-b border-stone-200">
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-baseline gap-4">
          <h1 className="font-display text-2xl font-bold text-pine-800">AIEF</h1>
          <p className="text-sm text-stone-500">AI Ethics Impact Framework — automated proposal assessment</p>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-10 space-y-8">
        {state === "idle" && (
          <div className="pt-8">
            <div className="max-w-3xl mx-auto mb-8 text-center">
              <h2 className="font-display text-3xl font-semibold text-stone-800 mb-3">
                From free-text proposal to structured ethics assessment
              </h2>
              <p className="text-sm text-stone-500 max-w-xl mx-auto">
                Grounded in a knowledge graph of 207 requirements across REAMS, the EU AI Act, Horizon Europe and
                ACM/NeurIPS guidelines, 70 real AI incidents, and EU Charter of Fundamental Rights mappings.
              </p>
            </div>
            {error && (
              <div className="max-w-3xl mx-auto mb-4 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}
            <ProposalInput onSubmit={assess} disabled={false} />
          </div>
        )}

        {state === "loading" && (
          <div className="pt-24 flex flex-col items-center gap-6">
            <div className="h-10 w-10 rounded-full border-4 border-pine-100 border-t-pine-700 animate-spin" />
            <ol className="space-y-2 text-sm">
              {STEPS.map((s, i) => (
                <li key={s} className={`flex items-center gap-2 ${i <= step ? "text-pine-800" : "text-stone-400"}`}>
                  <span
                    className={`h-5 w-5 rounded-full text-xs flex items-center justify-center ${
                      i < step ? "bg-pine-700 text-white" : i === step ? "border-2 border-pine-700 text-pine-700" : "border border-stone-300"
                    }`}
                  >
                    {i < step ? "✓" : i + 1}
                  </span>
                  {s}…
                </li>
              ))}
            </ol>
          </div>
        )}

        {state === "results" && result && (
          <>
            <div className="flex justify-end">
              <button
                onClick={() => { setResult(null); setState("idle") }}
                className="text-sm text-pine-700 hover:underline"
              >
                ← Assess another proposal
              </button>
            </div>
            <RiskBanner
              level={result.assessment.overall_risk_level}
              confidence={result.assessment.confidence_flag}
              reamsLikely={result.assessment.reams_clearance_likely}
            />
            <RiskSummary summary={result.assessment.risk_summary} />
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
              <div className="lg:col-span-3 space-y-8">
                <RiskCards risks={result.assessment.identified_risks} />
                <RequirementsTable requirements={result.assessment.applicable_requirements} />
                <Checklist title="Tier 1 mandatory actions" items={result.assessment.tier1_mandatory_actions} />
                <Checklist title="Tier 2 reflective prompts" items={result.assessment.tier2_reflective_prompts} />
              </div>
              <div className="lg:col-span-2 space-y-8">
                <CharterRights rights={result.assessment.charter_rights_at_risk} />
                <Incidents incidents={result.assessment.historical_precedents} />
                <Mitigations mitigations={result.assessment.recommended_mitigations} />
              </div>
            </div>
            <RetrievalPanel meta={result._retrieval_metadata} />
            <KGMetadata
              model={result.llm_model}
              backend={result.llm_backend}
              timestamp={result.timestamp}
              confidence={result.assessment.confidence_flag}
            />
          </>
        )}
      </div>
    </main>
  )
}
