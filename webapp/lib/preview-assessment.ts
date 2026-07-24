import type { AssessmentResponse } from "@/lib/types"

/** Sample payload for UI preview (`?preview=1`) — not used in production assessments. */
export const PREVIEW_ASSESSMENT: AssessmentResponse = {
  llm_backend: "preview",
  llm_model: "llama-3.3-70b-versatile",
  timestamp: new Date().toISOString(),
  assessment: {
    overall_risk_level: "High",
    confidence_flag: "HIGH",
    reams_clearance_likely: false,
    risk_summary:
      "Commercial health risk stratification may systematically underestimate needs of Black patients via cost proxies, without bias auditing or appeal mechanisms.",
    identified_risks: [
      {
        risk: "Bias against Black patients via cost proxy",
        severity: "High",
        explanation:
          "Historical cost underestimates need for patients facing structural barriers, risking unequal care referral.",
      },
      {
        risk: "No transparency or appeal path",
        severity: "High",
        explanation: "Automatic top-percentile referral without review or patient remedy.",
      },
      {
        risk: "Sensitive health data at scale",
        severity: "Medium",
        explanation: "Claims and EHR covering ~200M patients without clear protection detail.",
      },
      {
        risk: "Limited patient autonomy",
        severity: "Medium",
        explanation: "Automatic enrolment pathways without explicit consent.",
      },
    ],
    applicable_requirements: [
      {
        requirement_id: "ACM003",
        requirement_text: "Be fair and take action not to discriminate",
        framework: "ACMConference",
        tier: "Tier 1 Mandatory",
        action_needed: "Independent bias audit before deployment.",
      },
      {
        requirement_id: "ACM004",
        requirement_text: "Ameliorate biases in data and model outputs",
        framework: "ACMConference",
        tier: "Tier 1 Mandatory",
        action_needed: "Regular disparity audits on referral rates.",
      },
      {
        requirement_id: "AI001",
        requirement_text: "Ensure transparency, explainability and fairness",
        framework: "EUAIAct",
        tier: "Tier 1 Mandatory",
        action_needed: "Document decision logic and human oversight.",
      },
      {
        requirement_id: "HE002",
        requirement_text: "Design with human values in mind",
        framework: "HorizonEurope",
        tier: "Tier 1 Mandatory",
        action_needed: "Review design against fairness and accountability.",
      },
      {
        requirement_id: "R028",
        requirement_text: "Address equality and non-discrimination risks",
        framework: "REAMS",
        tier: "Tier 1 Mandatory",
        action_needed: "REAMS equality impact assessment required.",
      },
    ],
    charter_rights_at_risk: [
      {
        article: "Article 21",
        right_name: "Non-Discrimination",
        relevance: "Cost proxy may reproduce racial disparities in care access.",
      },
      {
        article: "Article 35",
        right_name: "Health Care",
        relevance: "Unequal referral may impair access to care management.",
      },
      {
        article: "Article 47",
        right_name: "Effective Remedy",
        relevance: "No appeal mechanism for non-referral decisions.",
      },
    ],
    historical_precedents: [
      {
        incident_id: "AIAAIC-001",
        incident_title: "Amazon Hiring Algorithm Gender Bias",
        lesson: "Audit systems for bias before deployment; fairness requires ongoing checks.",
      },
      {
        incident_id: "AIAAIC-047",
        incident_title: "Optum Health Algorithm Racial Bias",
        lesson: "Cost as proxy for need systematically underestimates Black patients' health needs.",
      },
    ],
    recommended_mitigations: [
      {
        mitigation: "Replace or augment cost proxy with clinical need measures; run race-stratified validation.",
        priority: "High",
      },
      {
        mitigation: "Add human review and patient appeal for non-referral decisions.",
        priority: "High",
      },
      {
        mitigation: "Publish model cards and disparity dashboards before rollout.",
        priority: "Medium",
      },
    ],
    tier1_mandatory_actions: [
      "Conduct independent bias auditing prior to deployment",
      "Implement measures to mitigate identified biases",
      "Establish algorithmic review and patient appeal routes",
    ],
    tier2_reflective_prompts: [
      "What harms arise if the cost proxy remains the primary need signal?",
      "How will affected communities contest or correct erroneous non-referrals?",
    ],
  },
  _retrieval_metadata: {
    rights_matched: 10,
    requirements_retrieved: 48,
    incidents_retrieved: 8,
    requirements_retrieved_ids: [
      "HE014",
      "R028",
      "ACM003",
      "ACM004",
      "AI001",
      "HE002",
      "R085",
      "ACM012",
      "AI016",
      "HE038",
    ],
    requirements_cited: ["ACM003", "ACM004", "AI001", "HE002", "R028"],
  },
}
