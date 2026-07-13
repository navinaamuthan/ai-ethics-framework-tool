"""
run_evaluation_groq.py
Deprecated wrapper — use run_evaluation.py with --backend groq instead.

  python3 run_evaluation.py --backend groq --model llama-3.3-70b-versatile --output-dir outputs_llama70b
"""

import sys

from run_evaluation import main

if __name__ == "__main__":
    if "--backend" not in sys.argv:
        sys.argv[1:1] = ["--backend", "groq"]
    if "--output-dir" not in sys.argv:
        sys.argv.extend(["--output-dir", "outputs/groq"])
    main()
