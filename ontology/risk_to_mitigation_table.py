"""
Risk-category -> mitigation-class rule table for the Week 1 mitigation-taxonomy
wiring (see CURSOR_MONTH_PLAN.md, Task 1.1).

Source of the 28 risk-category keys: every distinct value that appears as an
object of :hasRisk in ontology/ai-ethics-final.ttl, extracted directly from
the file (not invented). Verify this list still matches the ontology before
reusing the table if :hasRisk categories are ever added or renamed:

    grep -oE ':hasRisk\\s+[^.]+\\.' ai-ethics-final.ttl \\
        | grep -oE ':[A-Za-z]+' | grep -v '^:hasRisk$' | sort -u

Source of the 12 mitigation-class values: every :TechnicalMeasure and
:OrganisationalMeasure subclass declared in ontology/ai-ethics-final.ttl
(lines 166-180). No mitigation class is invented here; this table only
recombines what already exists in the ontology.

Each risk category maps to a short, ordered list of mitigation classes
(most-applicable first). A category maps to an empty list where none of the
12 existing classes plausibly addresses it -- this is intentional and must
be preserved. Do not pad these to force 100% coverage; the honest unmapped
count is itself a dissertation-reportable number (see CURSOR_MONTH_PLAN.md,
Task 1.1: "report the unmapped count honestly rather than padding coverage").

This same table is the single source of truth for two consumers:
  1. ontology/populate_mitigations.py (Week 1, Task 1.1) -- assigns
     :hasMitigation triples to requirements based on their existing :hasRisk
     values.
  2. shacl/aief-consistency-shapes.ttl's MitigationCategoryMatchShape
     (Week 2, Task 2.2) -- checks that an assessment's stated mitigation for
     a risk actually belongs to one of the classes listed here for that
     risk's category. Keep this file as the one place either consumer reads
     from, so the population script and the SHACL check can never drift
     apart from each other.
"""

RISK_TO_MITIGATION = {
    # --- Data / privacy risks: technical measures that act directly on data ---
    "PrivacyBreach":      [":Encryption", ":Pseudonymisation", ":AccessControl"],
    "DataBreach":         [":Encryption", ":AccessControl", ":AuditLog"],
    "DataGovernance":     [":AuditLog", ":GovernanceProcedure"],
    "Surveillance":       [":AccessControl", ":GovernanceProcedure", ":HumanOversight"],
    "FunctionCreep":      [":GovernanceProcedure", ":AuditLog"],

    # --- Identity / anonymity risks ---
    "FalseIdentification": [":Anonymisation", ":Pseudonymisation", ":HumanOversight"],

    # --- Fairness / rights risks: organisational and review-based measures ---
    "Discrimination":     [":StaffTraining", ":EthicsReviewBoard", ":AuditLog"],
    "GenderHarm":         [":StaffTraining", ":EthicsReviewBoard"],
    "ChildrenRights":     [":EthicsReviewBoard", ":HumanOversight", ":GovernanceProcedure"],
    "Dignity":            [":EthicsReviewBoard", ":StaffTraining"],

    # --- Physical / safety-critical risks: human oversight and incident response ---
    "PhysicalHarm":       [":HumanOversight", ":IncidentResponsePlan"],
    "WorkplaceSafetyRisk": [":HumanOversight", ":IncidentResponsePlan", ":StaffTraining"],
    "AddictionRisk":      [":HumanOversight", ":EthicsReviewBoard"],
    "PsychologicalHarm":  [":HumanOversight", ":EthicsReviewBoard"],

    # --- Liberty / due-process risks: appeal and oversight mechanisms ---
    "LibertyViolation":   [":ComplaintMechanism", ":HumanOversight"],
    "Manipulation":       [":ComplaintMechanism", ":EthicsReviewBoard"],
    "Deception":          [":ComplaintMechanism", ":ResponsibleReleasePolicy"],

    # --- Reputational / legal / dual-use risks: release-level governance ---
    "ReputationalHarm":   [":ResponsibleReleasePolicy", ":GovernanceProcedure"],
    "DualUseMisuse":      [":ResponsibleReleasePolicy", ":EthicsReviewBoard"],
    "IntellectualProperty": [":GovernanceProcedure"],

    # --- Economic / employment risks: organisational, not technical ---
    "EconomicHarm":       [":GovernanceProcedure", ":ComplaintMechanism"],
    "FinancialHarm":      [":GovernanceProcedure", ":AuditLog"],
    "EmploymentHarm":     [":StaffTraining", ":ComplaintMechanism"],

    # --- Democratic / expression / transparency risks: governance and disclosure ---
    "DemocraticProcessHarm": [":GovernanceProcedure", ":ResponsibleReleasePolicy"],
    "ExpressionHarm":     [":ComplaintMechanism", ":GovernanceProcedure"],
    "Transparency":       [":GovernanceProcedure", ":AuditLog"],
    "Accountability":     [":AuditLog", ":GovernanceProcedure", ":EthicsReviewBoard"],

    # --- Environmental risk: no existing mitigation class fits ---
    # None of the 12 classes (all data-handling, fairness-process, or
    # safety-oversight measures) plausibly address environmental impact.
    # Leave unmapped rather than force a bad fit -- flag as an ontology gap
    # in the dissertation update (Task 4.1), a legitimate small future-work
    # item (a 13th class, e.g. :EnvironmentalImpactAssessment).
    "EnvironmentalHarm":  [],
}

# Sanity checks a caller should run before using this table in Task 1.1 /
# Task 2.2 (not run automatically on import, since this module should have
# no side effects):
#
#   from risk_to_mitigation_table import RISK_TO_MITIGATION
#   assert len(RISK_TO_MITIGATION) == 28, "risk-category count drifted from ontology"
#   all_mitigation_classes = {
#       ":Encryption", ":Pseudonymisation", ":Anonymisation", ":AccessControl",
#       ":AuditLog", ":StaffTraining", ":GovernanceProcedure",
#       ":ComplaintMechanism", ":IncidentResponsePlan", ":EthicsReviewBoard",
#       ":HumanOversight", ":ResponsibleReleasePolicy",
#   }
#   for cats in RISK_TO_MITIGATION.values():
#       assert set(cats) <= all_mitigation_classes, "unknown mitigation class used"
