import { NextRequest, NextResponse } from "next/server"
import { retrieveFromKG } from "@/lib/kg-retrieval"
import { buildPrompt } from "@/lib/prompt-builder"
import { callLLM } from "@/lib/llm"

export const maxDuration = 60 // Vercel: allow up to 60s for LLM response

export async function POST(req: NextRequest) {
  const { proposalText, model } = await req.json()

  if (!proposalText || proposalText.trim().length < 50) {
    return NextResponse.json(
      { error: "Proposal text too short — enter at least 50 characters." },
      { status: 400 }
    )
  }

  try {
    // 1. KG retrieval
    const { requirements, incidents, matchedRights } = await retrieveFromKG(proposalText)

    // 2. Build prompt
    const prompt = buildPrompt(proposalText, requirements, incidents)

    // 3. LLM call
    const modelToUse = model || process.env.MODEL_NAME || "llama-3.3-70b-versatile"
    const rawResponse = await callLLM(prompt, modelToUse)

    // 4. Parse JSON (strip fences if the model added them anyway)
    const cleaned = rawResponse.replace(/```json|```/g, "").trim()
    const start = cleaned.indexOf("{")
    const end = cleaned.lastIndexOf("}")
    const assessment = JSON.parse(cleaned.slice(start, end + 1))

    // 5. Return with retrieval transparency metadata
    return NextResponse.json({
      llm_backend: process.env.USE_LIVE_KG === "true" ? "groq+graphdb" : "groq",
      llm_model: modelToUse,
      timestamp: new Date().toISOString(),
      assessment,
      _retrieval_metadata: {
        requirements_retrieved: requirements.length,
        incidents_retrieved: incidents.length,
        rights_matched: matchedRights.length,
        requirements_retrieved_ids: requirements.map((r) => r.id),
        requirements_cited:
          assessment.applicable_requirements?.map((r: any) => r.requirement_id) || [],
      },
    })
  } catch (err) {
    return NextResponse.json(
      { error: "Assessment failed", detail: String(err) },
      { status: 500 }
    )
  }
}
