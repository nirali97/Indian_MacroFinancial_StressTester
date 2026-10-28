# Project Guide — MacroFin StressTester

This guide is written as a practical walkthrough of how the project is organised and how I can run or explain it. The project is an educational simulation, not a production banking system.

## 1. What the project does

MacroFin StressTester explores how a small simulated financial system may react to economic shocks. It contains banks, micro/small businesses (MSMEs), consumers, loans, cash flows and shared macroeconomic indicators. A monthly simulation step updates these objects and records results in SQLite.

An XGBoost model estimates default risk for MSME loan applicants. The simulation can use this estimate as one input to a loan decision. A bank strategy agent changes risk appetite and lending limits. An optional RBI agent proposes repo-rate changes. These agents use deterministic rules when the optional Groq LLM is not configured or a response cannot be used.

## 2. System flow

1. The engine advances the month and applies active shocks.
2. Consumers and MSMEs earn, spend, make repayments or default under simplified rules.
3. The engine recalculates bank non-performing asset (NPA) ratios.
4. Active MSMEs can be considered for new loans. The oracle builds the feature row in the saved model's exact feature order and estimates default probability.
5. The current bank strategy adjusts the default-risk threshold. The engine records the decision and explanation, then transfers money if the loan is approved.
6. RBI and bank agents update policy/strategy values when their turn is reached.
7. The engine writes macro state, NPA ratios, decisions and explanations to SQLite.

The precise order is defined in `simulation/engine.py`; this list is a high-level overview.

## 3. Folder and file guide

### `simulation/`
- `engine.py` — coordinates each month, new loan decisions and database logging.
- `agents.py` — defines banks, MSMEs, consumers and loans, including simplified repayment/default behaviour.
- `ledger.py` — records transfers between entities.
- `world_state.py` — stores shared indicators such as GDP growth, inflation, repo rate, exchange rate and active shocks.
- `shocks.py` — applies and clears stress effects.

### `ml/`
- `oracle.py` — loads the saved XGBoost model and encoder artifacts, prepares an applicant row, predicts default probability and creates an explanation where possible.
- `train.py` — trains a replacement model from `data/msme_dataset.csv` and saves its model, encoder and feature schema. Training replaces the bundled model artifacts, so it should be run intentionally.
- `data_gen.py` — generates a new synthetic dataset if one is needed. Its labels are synthetic, not real observed defaults.

### `agents/`
- `rbi_governor.py` — asks Groq for a repo-rate suggestion, checks the response, and uses a rule-based fallback if needed.
- `bank_ceo.py` — asks Groq for each simulated bank's risk appetite and lending limit, with a rule-based fallback.
- `groq_setup.py` — loads `.env` settings and creates the shared Groq client without storing credentials in source code.

### `frontend/` and `scripts/`
- `frontend/app.py` — dashboard controls and charts. It also reads the supplied historical database separately.
- `scripts/run_sim.py` — runs a simulation from the terminal.
- `scripts/bootstrap.py` — checks for model/data files and avoids overwriting existing artifacts during normal setup.

### `data/`
- `npa_risk_model.json` — saved XGBoost model.
- `feature_names.json` — ordered list of input columns expected by the model.
- `label_encoders.joblib` — categorical encoders used with the original model.
- `msme_dataset.csv` — supplied 100,000-row dataset used for model training/evaluation.
- `simulation.db` — log database created/used by new runs.
- `simulation_history.db` — original supplied historical simulation logs. Keep it separate from new runs.

## 4. The model and its inputs

The bundled model is an XGBoost binary classifier. It returns a probability estimate for class `defaulted = 1`. Its nine input columns, in order, are `annual_revenue`, `cibil_score`, `existing_debt`, `import_dependent`, `employee_count`, `years_in_business`, `fixed_costs_monthly`, `sector_enc` and `region_enc`. The last two columns are categorical values encoded with the supplied sector and region encoders.

The oracle checks that the model feature schema agrees with `feature_names.json`. This matters because a model can load successfully but produce incorrect predictions if columns are accidentally swapped or filled with the wrong values. Unknown categories are encoded as `-1` by the original LabelEncoder-based artifacts.

The default decision threshold is 0.35. That threshold is a project setting, not a banking standard. The model score and the final simulated decision are not the same thing: bank strategy can adjust the threshold before the engine approves or rejects a loan.

If SHAP is installed and compatible, the oracle attempts to calculate per-applicant contributions. These values are in model-output space, not direct percentage-point changes in default probability. If that calculation fails, it reports model-level gain importance instead and labels it as a fallback; that fallback is not a per-applicant explanation.

## 5. Dataset and model training

The bundled dataset contains 100,000 rows and these fields: annual revenue, sector, region, CIBIL score, existing debt, import dependency, employee count, years in business, monthly fixed costs and the synthetic `defaulted` label. It contains no missing values in the supplied version. The labels are synthetic; a high ROC-AUC on this data would not prove performance on real businesses.

Normal setup runs `python scripts/bootstrap.py`, which keeps the existing model and dataset if they are present. To replace the model intentionally:

```bash
python -m ml.train
```

The training script prints held-out ROC-AUC and a classification report. Keep the generated model, feature schema and encoder together; do not copy only one artifact from a different training run.

## 6. Setup and run

Python 3.11 is recommended. From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/bootstrap.py
python -m pytest -q
```

Run the terminal simulation:

```bash
python scripts/run_sim.py --months 12 --shock NBFC_CRISIS
python scripts/run_sim.py --months 12 --no-ml --no-llm
```

Open the dashboard:

```bash
streamlit run frontend/app.py
```

Available shock names are `MONSOON_DEFICIT`, `NBFC_CRISIS`, `FII_PULLOUT` and `YES_BANK_SPIRAL`. To enable Groq, copy `.env.example` to `.env` and set `GROQ_API_KEY`; never commit the key. `GROQ_MODEL` can be changed if the configured model is no longer available. See `docs/GROQ_SETUP.md` for the exact steps. In the dashboard, check the decision `source` column: `Groq` means the response was accepted and `Rule-based fallback` means local rules were used.

## 7. Database and historical logs

New runs write to `data/simulation.db`. The supplied database is preserved as `data/simulation_history.db` and displayed separately in the dashboard. Keeping them separate prevents a new simulation run from overwriting the supplied historical months. SQLite tables include macro state history, NPA logs, agent decisions, model explanations and ledger transactions.

## 8. Tests and debugging

Run all tests with `python -m pytest -q`. If the oracle cannot load, check that the three model artifacts exist and that `xgboost`, `pandas` and `joblib` are installed. If a feature-schema mismatch is raised, do not simply remove the check: confirm that the model and feature list came from the same training run. If dashboard charts are empty, run at least one month and check `data/simulation.db`.

## 9. Limitations and responsible use

- The model labels are synthetic, so the predicted risk should not be used for real credit decisions.
- The economic rules and policy agents are illustrative, not calibrated against official RBI or bank supervisory models.
- Loan accounting, repayment, recovery and write-offs are simplified.
- The optional market snapshot uses data made available by Yahoo Finance; it is not guaranteed to be real-time.
- LLM services may be unavailable or return unsuitable responses, so deterministic fallbacks are used. Mocked tests check both successful response handling and fallback behaviour, but a live Groq call still requires your own API key.
- Do not use real customer personal or financial data in this project.

## 10. Suggested reading order

Start with this guide and `frontend/app.py` to see how the dashboard is used. Read `simulation/engine.py` next for the monthly flow, then `simulation/agents.py` and `simulation/ledger.py`. Read `ml/oracle.py` to understand how applicant data is prepared for the trained model, and `ml/train.py` only when you want to retrain it.
