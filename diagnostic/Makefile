# Diagnostic methodology pipeline — Steps 1–6
PYTHON ?= /Users/navinaamuthan/Dissertation/venv/bin/python
export PYTHONPATH := ../rag-pipeline:.

.PHONY: all step1 step2 step3 step4 step5 step6

all: step1 step2 step3 step4 step5 step6

step1:
	$(PYTHON) corpus_expansion.py

step2:
	$(PYTHON) frame_annotation.py --backend groq --temperature 0.7

step3:
	$(PYTHON) reliability_analysis.py

step4:
	$(PYTHON) perturbation_generator.py

step5:
	$(PYTHON) property_evaluator.py

step6:
	$(PYTHON) generate_tables.py
