"""Which authority template fields go unfilled across generated docs."""
from pathlib import Path
from collections import Counter
docs = Path(__file__).parent.parent / "evaluation/generated-documentation"
missing = Counter()
for f in docs.glob("*.md"):
    auth = f.stem.split("_", 1)[1]
    section = None
    for line in open(f):
        if line.startswith("## "): section = line[3:].strip()
        elif "[NOT DERIVABLE" in line: missing[(auth, section)] += 1
for (auth, field), n in missing.most_common():
    print(f"{auth:14s} {field:28s} unfilled in {n} docs")
