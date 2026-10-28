# Data and model notes

## Supplied artifacts

| File | Purpose |
|---|---|
| `data/msme_dataset.csv` | Supplied synthetic MSME dataset (100,000 rows) |
| `data/npa_risk_model.json` | Trained XGBoost classifier |
| `data/feature_names.json` | Exact model input order |
| `data/label_encoders.joblib` | Encoders for sector and region |
| `data/simulation_history.db` | Supplied historical simulation logs |
| `data/simulation.db` | Database for fresh simulation runs |

## Feature contract

The model expects: `annual_revenue`, `cibil_score`, `existing_debt`, `import_dependent`, `employee_count`, `years_in_business`, `fixed_costs_monthly`, `sector_enc`, `region_enc`. The categorical fields must be encoded using the encoder artifacts from the same training run. The oracle validates the saved feature list against the model feature names before scoring.

## Interpretation

A predicted probability is not proof of a future default. The dataset's `defaulted` column is synthetic, and model metrics measure fit to that data-generating process. SHAP contributions describe how features move the model output; they are not causal effects. If SHAP is unavailable, model gain importance is a global model statistic, not an individual explanation.

## Re-training warning

`python -m ml.train` replaces the bundled model, encoder and feature schema. Keep those files together and run tests after retraining. `python scripts/bootstrap.py` intentionally does not replace existing artifacts.
