# Gap verification log (Seam 1c)

Dual-IRI scan (`find_dual_iris.py`, 18 Jul 2026): **0 duplicates** after merging
`Art7_Privacy→Art7_PrivateLife` and `Art6_LibertyAndSecurity→Art6_RightToLiberty`.

Keyword search over all 207 requirement texts + inspection of near-miss mappings.
Source-document check: REAMS requirement texts in KG; ACM/NeurIPS and Horizon texts in KG;
AI Act Art. 27 FRIA requirements in KG (AI001–AI030). Full PDF manuals were not re-read
cover-to-cover; verification is against the extracted requirement set that populates AIEF.

| Right | Incidents | REAMS checked | AI Act | Horizon | ACM | Verdict |
|---|---|---|---|---|---|---|
| Art15_FreedomOfOccupation | 11 (HireVue, Deliveroo, LinkedIn ads, Robodebt, UC algorithm, …) | Employment/hire keywords hit collaborator/COI items only (R006/R007/R057); bias handled via Art21 (R085), not Art15 | No FRIA item names occupational freedom | Crowdworker items map to Art31, not Art15 | ACM011/ACM037 → Art31 | **genuine gap** — frameworks address hiring harm via non-discrimination / working conditions, never Art15 |
| Art48_PresumptionOfInnocence | 5 (COMPAS×3, Post Office Horizon, Rekognition Congress) | R068 (criminal conviction *data*) maps to Art7/Art8 only | No Art48 mapping among AI001–AI030 | None | None | **genuine gap** — criminal-data processing ≠ presumption of innocence |
| Art13_FreedomOfArtsScience | 1 (GitHub Copilot) | No arts/sciences freedom language | None | None | None | **genuine gap** |
| Art17_RightToProperty | 1 (GitHub Copilot) | — | — | — | ACM005 explicitly requires respecting IP / data/code ownership but was mapped only to Art3/7/8 | **mapping omission — corrected** (`ACM005 :mapsToRight :Art17_RightToProperty`, reloaded 18 Jul 2026) |

## Post-correction landscape

Harm-without-governance rights remaining: **3** (Art15, Art48, Art13).
Each was verified against the extracted requirement corpus to rule out further mapping omission.
