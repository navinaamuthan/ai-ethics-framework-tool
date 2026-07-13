export interface AssessmentResponse {
  proposal_id?: string
  mode?: string
  llm_backend: string
  llm_model: string
  timestamp: string
  assessment: Assessment
  _retrieval_metadata: RetrievalMetadata
}

export interface Assessment {
  overall_risk_level: "High" | "Medium" | "Low"
  confidence_flag: "HIGH" | "LOW"
  reams_clearance_likely: boolean
  risk_summary: string
  identified_risks: Risk[]
  applicable_requirements: Requirement[]
  charter_rights_at_risk: CharterRight[]
  historical_precedents: Incident[]
  recommended_mitigations: Mitigation[]
  tier1_mandatory_actions: string[]
  tier2_reflective_prompts: string[]
}

export interface Risk {
  risk: string
  severity: "High" | "Medium" | "Low"
  explanation: string
}

export type Framework = "REAMS" | "EUAIAct" | "HorizonEurope" | "ACMConference"

export interface Requirement {
  requirement_id: string
  requirement_text: string
  framework: Framework
  tier: "Tier 1 Mandatory" | "Tier 2 Reflective"
  action_needed: string
}

export interface CharterRight {
  article: string
  right_name: string
  relevance: string
}

export interface Incident {
  incident_id: string
  incident_title: string
  lesson: string
}

export interface Mitigation {
  mitigation: string
  priority: "High" | "Medium" | "Low"
}

export interface RetrievalMetadata {
  rights_matched: number
  requirements_retrieved: number
  incidents_retrieved: number
  requirements_retrieved_ids: string[]
  requirements_cited: string[]
}

// KG snapshot shapes
export interface KGRequirement {
  id: string
  text: string
  framework: Framework
  tier: string
  charter_articles?: string[]
  tags?: string[]
}

export interface KGIncident {
  id: string
  title: string
  description: string
  tags?: string[]
}

export interface KGSnapshot {
  requirements: KGRequirement[]
  incidents: KGIncident[]
}
