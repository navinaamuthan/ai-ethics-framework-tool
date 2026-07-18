"""Generate a blinded second-annotator sheet from synthetic proposal texts."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from synthetic_proposals import PROPOSALS

SRC = Path(__file__).parent.parent / "evaluation/results/llama-3.3-70b"
out_path = Path(__file__).parent / "annotation_sheet.md"
with open(out_path, "w") as out:
    out.write(
        "# AIEF second-annotator sheet\n"
        "For each proposal: risk level (High/Medium/Low) and applicable Charter articles "
        "(comma-separated, e.g. Article7, Article8).\n"
        "Do not consult the system or the first annotator.\n"
    )
    for gt in sorted(PROPOSALS, key=lambda p: p["id"]):
        pid = gt["id"]
        f = SRC / f"{pid}_full.json"
        text = json.load(open(f))["proposal_text"] if f.exists() else gt["proposal_text"]
        out.write(f"\n---\n## {pid}\n{text}\n\n**Risk level:** ____\n**Charter articles:** ____\n")
    out.write(
        "\n---\n## Mapping validity (agree/disagree)\n"
        "For each requirement→right mapping, mark A (agree) or D (disagree).\n\n"
        "| Req | Mapped right | A/D |\n|---|---|---|\n"
        "| R085 | Art21_NonDiscrimination |  |\n"
        "| R085 | Art20_EqualityBeforeLaw |  |\n"
        "| R042 | Art8_DataProtection |  |\n"
        "| R019 | Art7_PrivateLife |  |\n"
        "| ACM005 | Art17_RightToProperty |  |\n"
        "| ACM023 | Art21_NonDiscrimination |  |\n"
        "| AI001 | Art47_RightToEffectiveRemedy |  |\n"
        "| HE012 | Art21_NonDiscrimination |  |\n"
        "| R068 | Art8_DataProtection |  |\n"
        "| ACM011 | Art31_FairWorkingConditions |  |\n"
        "| R027 | Art8_DataProtection |  |\n"
        "| HE003 | Art1_HumanDignity |  |\n"
        "| AI016 | Art21_NonDiscrimination |  |\n"
        "| R071 | Art47_RightToEffectiveRemedy |  |\n"
        "| ACM001 | Art1_HumanDignity |  |\n"
        "| R054 | Art8_DataProtection |  |\n"
        "| HE015 | Art21_NonDiscrimination |  |\n"
        "| AI021 | Art41_GoodAdministration |  |\n"
        "| R010 | Art6_RightToLiberty |  |\n"
        "| ACM037 | Art31_FairWorkingConditions |  |\n"
    )
print(f"{out_path} written")
