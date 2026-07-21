"""
generate_tables.py
Emit LaTeX tables from diagnostic results JSON into results/tables/.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
TABLES = RESULTS / "tables"


def _fmt(x, nd=3):
    if x is None:
        return "---"
    if isinstance(x, float):
        if x != x:  # NaN
            return "---"
        return f"{x:.{nd}f}"
    return str(x)


def write(name: str, body: str) -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    path = TABLES / name
    path.write_text(body.strip() + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def tab_reliability_headline(rel: dict) -> None:
    h = rel["headline_test"]
    body = r"""
\begin{table}[htbp]
\centering
\caption{Headline reliability of the diagnostic: within- vs cross-stratum Cohen's $\kappa$ (risk labels).}
\label{tab:reliability_headline}
\begin{tabular}{lcc}
\toprule
Quantity & Risk $\kappa$ & 95\% bootstrap CI \\
\midrule
Mean within-stratum & """ + _fmt(h["within_risk"]["mean"]) + r""" & [""" + _fmt(h["within_risk"]["ci95"][0]) + r""", """ + _fmt(h["within_risk"]["ci95"][1]) + r"""] \\
Mean cross-stratum (run 1) & """ + _fmt(h["cross_risk"]["mean"]) + r""" & [""" + _fmt(h["cross_risk"]["ci95"][0]) + r""", """ + _fmt(h["cross_risk"]["ci95"][1]) + r"""] \\
Reliability ceiling (max within) & """ + _fmt(rel["ceiling_risk"]) + r""" & --- \\
Noise band ($1-\mathrm{ceiling}$) & """ + _fmt(rel["decision_rule"]["noise_band"]) + r""" & --- \\
\bottomrule
\end{tabular}
\end{table}
"""
    write("tab_reliability_headline.tex", body)


def tab_decision_rule(rel: dict) -> None:
    rows = []
    for p in rel["decision_rule"]["pairs"]:
        rows.append(
            f"{p['assessor_a']} vs {p['assessor_b']} & {_fmt(p['kappa_a'])} & {_fmt(p['kappa_b'])} & {_fmt(p['gap'])} & {p['verdict'].replace('_', ' ')} \\\\"
        )
    body = r"""
\begin{table}[htbp]
\centering
\caption{Decision rule: assessor-pair accuracy gaps vs noise band implied by the reliability ceiling.}
\label{tab:decision_rule}
\begin{tabular}{llccc}
\toprule
Pair & $\kappa_a$ & $\kappa_b$ & Gap & Verdict \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    write("tab_decision_rule.tex", body)


def tab_assessor_vs_gt(rel: dict) -> None:
    rows = []
    for name, row in rel["assessor_vs_gt"].items():
        rows.append(
            f"{name} & {row['n_proposals']} & {_fmt(row['risk_kappa'])} & {_fmt(row['rights_kappa'])} \\\\"
        )
    body = r"""
\begin{table}[htbp]
\centering
\caption{Assessor agreement with reference labels (Cohen's $\kappa$).}
\label{tab:assessor_vs_gt}
\begin{tabular}{lccc}
\toprule
Assessor & $n$ & Risk $\kappa$ & Rights $\kappa$ \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    write("tab_assessor_vs_gt.tex", body)


def tab_perturbation(pert: dict) -> None:
    rates = pert["sensitivity_rates"]
    rows = []
    for a, classes in rates.items():
        rows.append(
            f"{a} & {_fmt(classes['positive']['rate'])} & {_fmt(classes['negative']['rate'])} & {_fmt(classes['neutral']['rate'])} \\\\"
        )
    note = pert.get("scope_note", "").replace("&", r"\&")
    body = r"""
\begin{table}[htbp]
\centering
\caption{Perturbation sensitivity rates by assessor and class. """ + note + r"""}
\label{tab:perturbation_sensitivity}
\begin{tabular}{lccc}
\toprule
Assessor & Positive & Negative & Neutral \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    write("tab_perturbation_sensitivity.tex", body)


def tab_properties(prop: dict) -> None:
    names = ["LLM-8B", "LLM-70B", "SHACL", "keyword-baseline"]
    rows = []
    for n in names:
        rows.append(
            f"{n} & {_fmt(prop['stability'][n]['stability'])} & "
            f"{_fmt(prop['traceability'][n]['mean_traceable_fraction'])} & "
            f"{_fmt(prop['amendability'][n].get('mean_edit_size'))} & "
            f"{_fmt(prop['amendability'][n].get('mean_collateral'))} & "
            f"{_fmt(prop['comprehensibility'][n].get('mean_score'), 2)} \\\\"
        )
    body = r"""
\begin{table}[htbp]
\centering
\caption{Illustrative property scores (stability, traceability, amendability, comprehensibility).}
\label{tab:property_scores}
\begin{tabular}{lccccc}
\toprule
Assessor & Stability & Traceability & Edit size & Collateral & Compreh. \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    write("tab_property_scores.tex", body)


def main() -> None:
    rel = json.loads((RESULTS / "reliability_report.json").read_text())
    tab_reliability_headline(rel)
    tab_decision_rule(rel)
    tab_assessor_vs_gt(rel)

    pert_path = RESULTS / "perturbation_report.json"
    if pert_path.exists():
        tab_perturbation(json.loads(pert_path.read_text()))
    else:
        print("SKIP perturbation tables — report missing")

    prop_path = RESULTS / "property_report.json"
    if prop_path.exists():
        tab_properties(json.loads(prop_path.read_text()))
    else:
        print("SKIP property tables — report missing")

    print("Headline figures (copy into prose if needed):")
    print("  within_risk", rel["headline_test"]["within_risk"]["mean"])
    print("  cross_risk", rel["headline_test"]["cross_risk"]["mean"])
    print("  ceiling", rel["ceiling_risk"])
    print("  noise_band", rel["decision_rule"]["noise_band"])


if __name__ == "__main__":
    main()
