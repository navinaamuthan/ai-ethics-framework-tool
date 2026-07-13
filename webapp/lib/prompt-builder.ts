// lib/prompt-builder.ts — mirror of Python prompt_builder.py.
// If you change the prompt in the dissertation pipeline, change it here too.
import type { KGRequirement, KGIncident } from "./types"

export function buildPrompt(
  proposalText: string,
  requirements: KGRequirement[],
  incidents: KGIncident[]
): string {
  const reqBlock = requirements
    .map((r) => `- [${r.id}] (${r.framework}, ${r.tier}) ${r.text}`)
    .join("\n")

  const incBlock = incidents
    .map((i) => `- [${i.id}] ${i.title}: ${i.description}`)
    .join("\n")

  return `You are an AI research ethics assessor. Assess the following AI research proposal against the retrieved regulatory requirements and historical AI incident precedents.

RESEARCH PROPOSAL:
${proposalText}

RETRIEVED REQUIREMENTS (from the AIEF knowledge graph — cite requirement IDs verbatim):
${reqBlock}

RETRIEVED HISTORICAL AI INCIDENTS (AIAAIC registry — cite incident IDs verbatim):
${incBlock}

TASK:
Produce a structured ethics assessment. Classify overall risk as High, Medium, or Low. Identify concrete risks, applicable requirements (only from the retrieved list, citing their exact IDs), EU Charter of Fundamental Rights articles at risk, relevant historical precedents (only from the retrieved list), and recommended mitigations. Separate Tier 1 mandatory actions from Tier 2 reflective prompts. Set confidence_flag to HIGH if retrieval provided strong coverage of the proposal's risk areas, otherwise LOW. Set reams_clearance_likely based on whether the proposal would plausibly pass TCD REAMS review as described.

Respond with ONLY a JSON object (no markdown fences, no preamble) with exactly this schema:
{
  "overall_risk_level": "High" | "Medium" | "Low",
  "confidence_flag": "HIGH" | "LOW",
  "reams_clearance_likely": true | false,
  "risk_summary": "one paragraph",
  "identified_risks": [{"risk": "...", "severity": "High|Medium|Low", "explanation": "..."}],
  "applicable_requirements": [{"requirement_id": "...", "requirement_text": "...", "framework": "REAMS|EUAIAct|HorizonEurope|ACMConference", "tier": "Tier 1 Mandatory|Tier 2 Reflective", "action_needed": "..."}],
  "charter_rights_at_risk": [{"article": "Article N", "right_name": "...", "relevance": "..."}],
  "historical_precedents": [{"incident_id": "...", "incident_title": "...", "lesson": "..."}],
  "recommended_mitigations": [{"mitigation": "...", "priority": "High|Medium|Low"}],
  "tier1_mandatory_actions": ["..."],
  "tier2_reflective_prompts": ["..."]
}`
}
