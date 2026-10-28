# MacroFin StressTester

MacroFin StressTester is an educational macro-financial simulation. It models a small banking system, MSME businesses and consumers, applies economic stress scenarios, and records the resulting decisions and indicators. It combines an XGBoost-based MSME default-risk estimate with agent-based simulation and optional Groq LLM policy suggestions.

## What is included

- A pre-trained XGBoost credit-risk model and the feature schema it expects.
- The supplied label encoders and 100,000-row MSME dataset.
- An agent-based simulation for banks, MSMEs, consumers and loans.
- Economic shocks: `MONSOON_DEFICIT`, `NBFC_CRISIS`, `FII_PULLOUT` and `YES_BANK_SPIRAL`.
- A Groq-powered RBI Governor agent and bank strategy agents, with rule-based fallback when Groq is not configured or a response fails.
- A SQLite ledger and logs for macro indicators, bank NPA ratios, decision sources and model explanations.
- The supplied historical simulation database, kept separate from new runs.
- Automated tests and step-by-step documentation.

## Setup

Python 3.11 is recommended. Run these commands from the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/bootstrap.py
python -m pytest -q
```

## Set up Groq (optional)

1. Create an API key at [Groq Console](https://console.groq.com/keys).
2. Run `cp .env.example .env` from the project root.
3. Put your key in the `GROQ_API_KEY` value in `.env`. Keep the file private; it is ignored by Git.
4. Check `GROQ_MODEL` in `.env.example` and use a model currently available to your account if the default changes.
5. Run `python scripts/run_sim.py --months 2`, or launch the dashboard with `streamlit run frontend/app.py`.
6. In the dashboard's **Agent decisions** tab, check the `source` column. `Groq` means the response was accepted; `Rule-based fallback` means the simulation used local rules instead.

The key is not bundled in this ZIP and should never be committed to GitHub. See [`docs/GROQ_SETUP.md`](docs/GROQ_SETUP.md) for troubleshooting. To disable all LLM calls, use `python scripts/run_sim.py --months 2 --no-llm`.

## Run the simulation

```bash
python scripts/run_sim.py --months 12 --shock NBFC_CRISIS
python scripts/run_sim.py --months 12 --no-ml --no-llm
streamlit run frontend/app.py
```

The dashboard can run one month at a time, activate/clear a stress scenario, and show macro indicators, bank NPA ratios, agent decisions and recent loan explanations. New simulation logs are written to `data/simulation.db`; the supplied historical logs are preserved in `data/simulation_history.db`.

## Main folders

- `simulation/` — simulation state, participants, monthly engine, money transfers and stress scenarios.
- `ml/` — dataset generator, model training and loan-scoring oracle.
- `agents/` — RBI and bank strategy agents, plus shared Groq setup.
- `frontend/` — Streamlit dashboard.
- `data/` — model artifacts, dataset and SQLite databases.
- `scripts/` — setup and command-line run helpers.
- `tests/` — automated checks, including mocked LLM responses (no API key required).
- `docs/` — project guide, architecture, data/model notes, testing and Groq setup.

## Important limitations

The model was trained on synthetic labels and its predictions are not validated for real lending. The macro simulation is illustrative, not an official or calibrated bank stress test. Payment, default, recovery and policy mechanisms are simplified. SHAP values are explanations in model-output space; when SHAP is unavailable, the system shows model-level gain importance instead and labels that fallback. Market data from yfinance is not guaranteed real-time data. Do not use real customer personal or financial data.
