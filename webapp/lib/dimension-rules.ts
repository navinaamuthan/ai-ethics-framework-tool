// Mirrors shacl/aief-risk-shapes.ttl (source of truth). Keep in sync manually.
export type Finding = {
  rule: string
  dimension: string
  priority: 1 | 2 | 3
  severity: "violation" | "warning"
}

const has = (t: string, ...rx: RegExp[]) => rx.some((r) => r.test(t))

export function dimensionProfile(text: string): Finding[] {
  const t = text.toLowerCase()
  const out: Finding[] = []
  const biometric = has(t, /biometric|facial recogn|fingerprint/)
  const consent = has(t, /opt-in consent|informed consent obtained|consent will be obtained/)
  if (biometric && !consent)
    out.push({
      rule: "Biometric data requires opt-in consent",
      dimension: "Article 8",
      priority: 1,
      severity: "violation",
    })
  if (
    (biometric || has(t, /health|medical|clinical|mental/)) &&
    !has(t, /dpia|data protection impact assessment/)
  )
    out.push({
      rule: "Special-category data requires a DPIA",
      dimension: "Article 8",
      priority: 1,
      severity: "violation",
    })
  if (
    has(t, /facial recogn|clinical decision|diagnos|triage|hiring|recruit|screening/) &&
    !has(t, /bias audit|audited for.*bias/)
  )
    out.push({
      rule: "Models affecting people require an independent bias audit",
      dimension: "Article 21",
      priority: 2,
      severity: "violation",
    })
  if (
    has(t, /child|minor|school pupils|under 18/) &&
    has(t, /monitor|surveil|cctv|track/) &&
    !has(t, /opt-out/)
  )
    out.push({
      rule: "Monitoring of minors requires an individual opt-out",
      dimension: "Article 24",
      priority: 1,
      severity: "violation",
    })
  if (has(t, /clinical decision|diagnos|triage/) && !has(t, /clinical (validation|trial)/))
    out.push({
      rule: "Clinical decision support requires clinical validation",
      dimension: "Article 35",
      priority: 2,
      severity: "warning",
    })
  if (has(t, /chatbot|conversational/) && !has(t, /disclaimer|disclosed? (that|as) (an )?ai/))
    out.push({
      rule: "Users must know they are interacting with an AI",
      dimension: "Article 1",
      priority: 3,
      severity: "warning",
    })
  return out.sort((a, b) => a.priority - b.priority)
}
