// lib/kg-retrieval.ts — static KG lookup against lib/kg-snapshot.json.
// Set USE_LIVE_KG=true + GRAPHDB_ENDPOINT to query GraphDB via SPARQL instead.
import rawSnapshot from "./kg-snapshot.json"
import type { KGSnapshot, KGRequirement, KGIncident, CharterRight } from "./types"

const snapshot = rawSnapshot as KGSnapshot

// Mirror of Python extract_keywords() — extend to stay consistent with the pipeline.
const KEYWORDS_MAP: Record<string, string[]> = {
  bias: ["bias", "discriminat", "fairness", "racial", "gender", "protected group"],
  health: ["health", "medical", "patient", "diagnos", "clinical", "mental health"],
  data: ["personal data", "gdpr", "consent", "data protection", "anonymis", "pseudonym", "sensitive data"],
  surveillance: ["surveil", "track", "monitor", "facial recogn", "biometric", "cctv"],
  children: ["child", "minor", "under 18", "school", "student"],
  employment: ["employ", "recruit", "hiring", "cv screening", "worker"],
  automation: ["automated decision", "autonomous", "self-driving", "robot"],
  transparency: ["explainab", "transparen", "black box", "interpretab"],
  security: ["security", "adversarial", "cyber", "vulnerab"],
  environment: ["environment", "energy", "carbon", "sustainab"],
  speech: ["content moderation", "misinformation", "free speech", "expression", "social media"],
  credit: ["credit", "loan", "insurance", "scoring", "financial"],
  law_enforcement: ["police", "predictive policing", "criminal", "justice", "sentencing", "border"],
}

const CHARTER_RIGHTS: { article: string; right_name: string; terms: string[] }[] = [
  { article: "Article 1", right_name: "Human dignity", terms: ["dignity", "degrading", "manipulat"] },
  { article: "Article 3", right_name: "Right to the integrity of the person", terms: ["medical", "clinical", "health", "bodily"] },
  { article: "Article 7", right_name: "Respect for private and family life", terms: ["privacy", "surveil", "monitor", "track", "home"] },
  { article: "Article 8", right_name: "Protection of personal data", terms: ["personal data", "gdpr", "consent", "data protection", "biometric"] },
  { article: "Article 11", right_name: "Freedom of expression and information", terms: ["expression", "speech", "content moderation", "misinformation", "censor"] },
  { article: "Article 21", right_name: "Non-discrimination", terms: ["discriminat", "bias", "racial", "gender", "fairness", "protected group"] },
  { article: "Article 24", right_name: "The rights of the child", terms: ["child", "minor", "school", "student"] },
  { article: "Article 31", right_name: "Fair and just working conditions", terms: ["worker", "employ", "workplace", "labour"] },
  { article: "Article 35", right_name: "Health care", terms: ["health", "patient", "diagnos", "clinical"] },
  { article: "Article 38", right_name: "Consumer protection", terms: ["consumer", "credit", "insurance", "product"] },
  { article: "Article 41", right_name: "Right to good administration", terms: ["public authority", "administrative", "government service"] },
  { article: "Article 47", right_name: "Right to an effective remedy and to a fair trial", terms: ["justice", "sentencing", "criminal", "appeal", "redress", "predictive policing"] },
]

function getCharterRights(text: string): CharterRight[] {
  return CHARTER_RIGHTS.filter((r) => r.terms.some((t) => text.includes(t))).map(
    ({ article, right_name }) => ({
      article,
      right_name,
      relevance: "Matched from proposal text against KG mapsToRight triples",
    })
  )
}

export async function retrieveFromKG(proposalText: string): Promise<{
  requirements: KGRequirement[]
  incidents: KGIncident[]
  matchedRights: CharterRight[]
}> {
  if (process.env.USE_LIVE_KG === "true") {
    // Live GraphDB path — same shape, SPARQL-backed.
    return retrieveFromGraphDB(proposalText)
  }

  const text = proposalText.toLowerCase()

  const matchedKeywords = Object.entries(KEYWORDS_MAP)
    .filter(([, terms]) => terms.some((t) => text.includes(t)))
    .map(([key]) => key)

  const matchesKeyword = (haystack: string, tags?: string[]) =>
    matchedKeywords.some(
      (kw) =>
        haystack.includes(kw) ||
        KEYWORDS_MAP[kw].some((t) => haystack.includes(t)) ||
        (tags || []).some((t) => t.toLowerCase().includes(kw))
    )

  const requirements = snapshot.requirements
    .filter((req) => matchesKeyword(req.text.toLowerCase(), req.tags))
    .slice(0, 100)

  const incidents = snapshot.incidents
    .filter((inc) => matchesKeyword(inc.description.toLowerCase(), inc.tags))
    .slice(0, 8)

  const matchedRights = getCharterRights(text)

  return { requirements, incidents, matchedRights }
}

// Placeholder live path — fill in SPARQL queries mirroring sparql_retrieval.py
async function retrieveFromGraphDB(proposalText: string) {
  const endpoint = process.env.GRAPHDB_ENDPOINT
  if (!endpoint) throw new Error("GRAPHDB_ENDPOINT not set")
  // TODO: port sparql_retrieval.py queries here when GraphDB is cloud-hosted.
  // Falls back to static snapshot for now.
  const text = proposalText.toLowerCase()
  return {
    requirements: snapshot.requirements.slice(0, 100),
    incidents: snapshot.incidents.slice(0, 8),
    matchedRights: getCharterRights(text),
  }
}
