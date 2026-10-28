"""Loads the saved XGBoost model and estimates an MSME applicant's default risk."""

from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier


class LoanOracle:
    """Score applicants with the bundled model; this is not a real credit decision."""

    def __init__(self, model_path="data/npa_risk_model.json",
                 feature_path="data/feature_names.json",
                 encoder_path="data/label_encoders.joblib", threshold=0.35):
        for path in (model_path, feature_path, encoder_path):
            if not Path(path).exists():
                raise FileNotFoundError(
                    f"Missing model artifact: {path}. Check the data folder or run python scripts/bootstrap.py."
                )
        self.model = XGBClassifier()
        self.model.load_model(model_path)
        self.features = json.loads(Path(feature_path).read_text())
        self.encoder = joblib.load(encoder_path)
        self.threshold = float(threshold)
        model_features = self.model.get_booster().feature_names
        if model_features and model_features != self.features:
            raise ValueError(f"Feature schema mismatch: model={model_features}, file={self.features}")
        self.last_explanation = {}

    def _encode_category(self, column, value):
        # Support the original dict of LabelEncoders and the OrdinalEncoder used by retraining.
        if isinstance(self.encoder, dict):
            encoder = self.encoder.get(column)
            if encoder is None:
                return -1.0
            try:
                return float(encoder.transform([str(value)])[0])
            except ValueError:
                return -1.0
        try:
            return float(self.encoder.transform(pd.DataFrame(
                [[str(value) for value in (self._category_values or [])]],
                columns=self._category_values
            )))
        except Exception:
            # OrdinalEncoder supports both categories together; handled in _frame below.
            return -1.0

    def _frame(self, applicant):
        # Fill in missing fields so the model always receives the columns it was trained on.
        row = dict(applicant)
        defaults = {
            "annual_revenue": 5000, "cibil_score": 650, "existing_debt": 0,
            "import_dependent": 0, "employee_count": 10, "years_in_business": 3,
            "fixed_costs_monthly": 200, "sector": "Services", "region": "Urban",
        }
        for key, value in defaults.items():
            row.setdefault(key, value)

        # The original project saved separate encoders; the retraining script can save one encoder.
        # Handle both formats here so the saved model and its encoders stay paired.
        if isinstance(self.encoder, dict):
            row["sector_enc"] = self._encode_category("sector", row["sector"])
            row["region_enc"] = self._encode_category("region", row["region"])
        else:
            # Older retrained artifacts may use a single sklearn OrdinalEncoder.
            try:
                encoded = self.encoder.transform(pd.DataFrame(
                    [[str(row["sector"]), str(row["region"])]], columns=["sector", "region"]
                ))[0]
                row["sector_enc"], row["region_enc"] = map(float, encoded)
            except Exception as exc:
                raise ValueError(f"Could not encode sector/region: {exc}") from exc

        return pd.DataFrame([{name: float(row.get(name, 0)) for name in self.features}],
                            columns=self.features)

    def assess(self, applicant):
        # Keep the feature order identical to feature_names.json before asking XGBoost to score it.
        frame = self._frame(applicant)
        probability = float(self.model.predict_proba(frame)[0][1])
        try:
            import shap
            values = np.asarray(shap.TreeExplainer(self.model).shap_values(frame))
            values = values.reshape(-1, len(self.features))[0]
            explanation = {name: {"shap_contribution": float(value)}
                           for name, value in zip(self.features, values)}
            explanation_note = "SHAP contributions are in model-output space, not percentage points."
        except Exception:
            gains = self.model.get_booster().get_score(importance_type="gain")
            explanation = {name: {"importance_gain": float(gains.get(name, 0.0))}
                           for name in self.features}
            explanation_note = "SHAP was unavailable; values show model gain importance, not per-applicant explanations."
        self.last_explanation = explanation
        return {"prob_default": probability,
                "decision": "REJECTED" if probability >= self.threshold else "APPROVED",
                "threshold": self.threshold, "shap": explanation,
                "explanation_note": explanation_note}
