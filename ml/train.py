"""Train a replacement XGBoost model from data/msme_dataset.csv."""

from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder
from sklearn.metrics import roc_auc_score, classification_report
from xgboost import XGBClassifier

DATA = Path("data/msme_dataset.csv")
MODEL = Path("data/npa_risk_model.json")
ENCODERS = Path("data/label_encoders.joblib")
FEATURES = Path("data/feature_names.json")
CATEGORICAL = ["sector", "region"]
NUMERIC = ["annual_revenue", "cibil_score", "existing_debt", "import_dependent",
           "employee_count", "years_in_business", "fixed_costs_monthly"]
ALL_FEATURES = NUMERIC + ["sector_enc", "region_enc"]

def train():
    """Train, print held-out metrics, and replace the saved model artifacts."""
    if not DATA.exists():
        raise FileNotFoundError(f"Training data not found: {DATA}. Restore the bundled CSV first.")
    df = pd.read_csv(DATA)
    encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    encoded = encoder.fit_transform(df[CATEGORICAL].astype(str))
    df["sector_enc"], df["region_enc"] = encoded[:, 0], encoded[:, 1]
    X = df[ALL_FEATURES].astype(float)
    y = df["defaulted"].astype(int)
    x_train, x_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)
    negatives = max(1, int((y_train == 0).sum()))
    positives = max(1, int((y_train == 1).sum()))
    model = XGBClassifier(n_estimators=250, max_depth=4, learning_rate=0.05,
        subsample=0.85, colsample_bytree=0.85, scale_pos_weight=negatives/positives,
        eval_metric="logloss", random_state=42, n_jobs=2)
    model.fit(x_train, y_train)
    probs = model.predict_proba(x_test)[:, 1]
    print(f"ROC-AUC: {roc_auc_score(y_test, probs):.3f}")
    print(classification_report(y_test, (probs >= 0.35).astype(int), zero_division=0))
    joblib.dump(encoder, ENCODERS)
    FEATURES.write_text(json.dumps(ALL_FEATURES, indent=2))
    model.save_model(str(MODEL))
    print("Saved replacement model, encoder and feature schema under data/.")
    return model

if __name__ == "__main__":
    train()
