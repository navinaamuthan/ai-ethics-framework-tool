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
import DimensionProfile from "@/components/DimensionProfile"
import { Panel } from "@/components/ui"
import { dimensionProfile, type Finding } from "@/lib/dimension-rules"
import { PREVIEW_ASSESSMENT } from "@/lib/preview-assessment"

const STEPS = ["Extracting keywords", "Querying knowledge graph", "Generating assessment"]

export default function Home() {
  const [state, setState] = useState<"idle" | "loading" | "results">("idle")
  const [step, setStep] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AssessmentResponse | null>(null)
  const [dimFindings, setDimFindings] = useState<Finding[]>([])

  useEffect(() => {
    if (typeof window === "undefined") return
    if (new URLSearchParams(window.location.search).get("preview") !== "1") return
    setResult(PREVIEW_ASSESSMENT)
    setDimFindings(
      dimensionProfile(
        "health risk stratification algorithm insurance claims bias Black patients race care management appeal"
      )
    )
    setState("results")
  }, [])

  useEffect(() => {
    if (state !== "loading") return
    setStep(0)
    const t1 = setTimeout(() => setStep(1), 900)
    const t2 = setTimeout(() => setStep(2), 2200)
    return () => {
      clearTimeout(t1)
      clearTimeout(t2)
    }
  }, [state])

  async function assess(proposalText: string, model: string) {
    setError(null)
    setState("loading")
    setDimFindings(dimensionProfile(proposalText))
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

  if (state === "results" && result) {
    const a = result.assessment
    return (
      <main className="flex min-h-dvh flex-col bg-[#f4f7f5] md:h-dvh md:overflow-hidden">
        <header className="flex shrink-0 items-center gap-3 border-b-2 border-stone-200 bg-white px-4 py-2">
          <h1 className="font-display text-lg font-bold tracking-tight text-pine-800">AIEF</h1>
          <span className="hidden text-[11px] text-stone-500 sm:inline">Ethics assessment report</span>
          <button
            onClick={() => {
              setResult(null)
              setState("idle")
              if (typeof window !== "undefined") {
                const url = new URL(window.location.href)
                url.searchParams.delete("preview")
                window.history.replaceState({}, "", url.pathname)
              }
            }}
            className="ml-auto rounded border-2 border-pine-700/20 bg-pine-50 px-3 py-1 text-[11px] font-semibold text-pine-800 transition hover:border-pine-700 hover:bg-pine-100"
          >
            ← Assess another
          </button>
        </header>

        <div className="flex min-h-0 flex-1 flex-col gap-1.5 p-2.5">
          <RiskBanner
            level={a.overall_risk_level}
            confidence={a.confidence_flag}
            reamsLikely={a.reams_clearance_likely}
          />
          <RiskSummary summary={a.risk_summary} />

          <div className="grid min-h-0 flex-1 grid-cols-1 gap-1.5 md:grid-cols-12 md:grid-rows-[minmax(0,1fr)_minmax(0,1.1fr)_minmax(0,0.75fr)]">
            <Panel
              title="Identified risks"
              count={a.identified_risks?.length}
              accent="border-l-red-600"
              className="min-h-0 md:col-span-4 md:row-start-1"
            >
              <RiskCards risks={a.identified_risks} />
            </Panel>

            <Panel
              title="Deterministic dimensions"
              count={dimFindings.length}
              accent="border-l-amber-600"
              className="min-h-0 md:col-span-4 md:row-start-1"
            >
              <DimensionProfile findings={dimFindings} />
            </Panel>

            <Panel
              title="Charter rights"
              count={a.charter_rights_at_risk?.length}
              accent="border-l-pine-700"
              className="min-h-0 md:col-span-4 md:row-start-1"
            >
              <CharterRights rights={a.charter_rights_at_risk} />
            </Panel>

            <Panel
              title="Applicable requirements"
              count={a.applicable_requirements?.length}
              accent="border-l-blue-600"
              scroll={false}
              className="min-h-0 md:col-span-7 md:row-start-2"
            >
              <RequirementsTable requirements={a.applicable_requirements} />
            </Panel>

            <Panel
              title="Precedents"
              count={a.historical_precedents?.length}
              accent="border-l-stone-500"
              className="min-h-0 md:col-span-2 md:row-start-2"
            >
              <Incidents incidents={a.historical_precedents} />
            </Panel>

            <Panel
              title="Mitigations"
              count={a.recommended_mitigations?.length}
              accent="border-l-green-600"
              className="min-h-0 md:col-span-3 md:row-start-2"
            >
              <Mitigations mitigations={a.recommended_mitigations} />
            </Panel>

            <Panel
              title="Actions & prompts"
              accent="border-l-pine-800"
              className="min-h-0 md:col-span-12 md:row-start-3"
            >
              <div className="grid gap-3 sm:grid-cols-2">
                <Checklist title="Tier 1 mandatory" items={a.tier1_mandatory_actions} />
                <Checklist title="Tier 2 reflective" items={a.tier2_reflective_prompts} />
              </div>
            </Panel>
          </div>

          <RetrievalPanel meta={result._retrieval_metadata} />
          <KGMetadata
            model={result.llm_model}
            backend={result.llm_backend}
            timestamp={result.timestamp}
            confidence={a.confidence_flag}
          />
        </div>
      </main>
    )
  }

  return (
    <main className="relative min-h-dvh overflow-hidden idle-atmosphere">
      <div className="idle-orb idle-orb-a" aria-hidden />
      <div className="idle-orb idle-orb-b" aria-hidden />
      <div className="idle-orb idle-orb-c" aria-hidden />
      <div
        className="idle-ring"
        style={{ width: "42rem", height: "42rem", top: "-12%", right: "-8%" }}
        aria-hidden
      />
      <div
        className="idle-ring"
        style={{ width: "28rem", height: "28rem", bottom: "5%", left: "-6%", animationDelay: "-4s" }}
        aria-hidden
      />
      <div className="pointer-events-none absolute inset-0 idle-slash" aria-hidden />
      <div className="pointer-events-none absolute inset-0 idle-grid" aria-hidden />

      <div
        className="pointer-events-none absolute inset-x-0 top-[6%] select-none text-center font-display text-[clamp(5.5rem,20vw,15rem)] font-bold leading-none tracking-tight text-pine-900/[0.08]"
        aria-hidden
      >
        AIEF
      </div>

      <header className="relative z-10 border-b-2 border-pine-900/15 bg-white/55 backdrop-blur-md">
        <div className="mx-auto flex max-w-5xl items-baseline gap-4 px-6 py-4">
          <h1 className="font-display text-2xl font-bold tracking-tight text-pine-800">AIEF</h1>
          <p className="text-sm text-stone-600">AI Ethics Impact Framework</p>
        </div>
      </header>

      <div className="relative z-10 mx-auto flex min-h-[calc(100dvh-4.5rem)] max-w-5xl flex-col justify-center px-6 py-10">
        {state === "idle" && (
          <>
            <div className="rise-in mb-8 text-center">
              <p className="mb-4 inline-flex items-center gap-2 rounded border-2 border-pine-800 bg-pine-800 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-white shadow-[3px_3px_0_0_#143124]">
                Knowledge-graph grounded
              </p>
              <h2 className="font-display text-5xl font-bold tracking-tight text-pine-900 sm:text-6xl">
                AIEF
              </h2>
              <p className="mx-auto mt-4 max-w-lg text-[15px] leading-relaxed text-stone-700">
                From free-text proposal to structured ethics assessment — 207 requirements, 70 AI incidents, and EU
                Charter rights mappings.
              </p>
            </div>

            {error && (
              <div className="rise-in-delay-1 mx-auto mb-4 max-w-2xl rounded-lg border-2 border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="rise-in rise-in-delay-2">
              <ProposalInput onSubmit={assess} disabled={false} />
            </div>
          </>
        )}

        {state === "loading" && (
          <div className="flex flex-col items-center gap-6 py-16">
            <div className="h-14 w-14 rounded-full border-[3px] border-pine-100 border-t-pine-700 animate-spin" />
            <ol className="space-y-2.5 text-sm">
              {STEPS.map((s, i) => (
                <li
                  key={s}
                  className={`flex items-center gap-2.5 ${i <= step ? "text-pine-800" : "text-stone-400"}`}
                >
                  <span
                    className={`flex h-6 w-6 items-center justify-center rounded text-xs font-bold ${
                      i < step
                        ? "bg-pine-700 text-white"
                        : i === step
                          ? "border-2 border-pine-700 text-pine-700"
                          : "border border-stone-300"
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
      </div>
    </main>
  )
}
