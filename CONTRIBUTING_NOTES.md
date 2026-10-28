# Contributing and making changes

This is a student project, so I try to keep changes small and easy to trace.

1. Create and activate the virtual environment described in `README.md`.
2. Read `docs/PROJECT_GUIDE.md` before changing the simulation flow.
3. Make one focused change at a time. Keep the existing module boundaries where possible.
4. Run `python -m pytest -q` after code changes.
5. If the model feature order or categorical encoding changes, update `ml/oracle.py`, `ml/train.py`, `data/feature_names.json`, and the relevant tests together.
6. Do not overwrite `data/simulation_history.db`; it is the supplied historical record. New runs use `data/simulation.db`.
7. Do not commit API keys or real customer data.

Use short docstrings to explain why a function exists or what it returns. Avoid comments that simply repeat the next line of code.
