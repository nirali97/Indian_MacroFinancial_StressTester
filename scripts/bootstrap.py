"""Check model artifacts and only create replacements when files are missing."""

from pathlib import Path
from ml.data_gen import generate_dataset
from ml.train import train

if __name__ == "__main__":
    required = [Path("data/npa_risk_model.json"), Path("data/feature_names.json"),
                Path("data/label_encoders.joblib"), Path("data/msme_dataset.csv")]
    missing = [path for path in required if not path.exists()]
    if not missing:
        print("Existing model, encoders, feature schema and dataset found; leaving them unchanged.")
        print("To intentionally retrain the model, run: python -m ml.train")
    else:
        print("Missing artifacts:", ", ".join(map(str, missing)))
        if not Path("data/msme_dataset.csv").exists():
            generate_dataset()
        train()
