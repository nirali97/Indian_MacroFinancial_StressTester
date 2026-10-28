"""Checks that the bundled model artifacts can score an applicant consistently."""

from pathlib import Path

from ml.oracle import LoanOracle


def test_oracle_uses_expected_feature_order_and_encodes_categories():
    oracle = LoanOracle()
    frame = oracle._frame({"sector": "Services", "region": "Urban"})

    assert list(frame.columns) == oracle.features
    assert "sector_enc" in frame.columns
    assert "region_enc" in frame.columns
    assert frame.loc[0, "sector_enc"] == 4
    assert frame.loc[0, "region_enc"] == 2


def test_oracle_returns_probability_and_decision():
    oracle = LoanOracle()
    result = oracle.assess({
        "annual_revenue": 12000,
        "cibil_score": 760,
        "existing_debt": 1000,
        "import_dependent": 0,
        "employee_count": 20,
        "years_in_business": 8,
        "fixed_costs_monthly": 150,
        "sector": "Services",
        "region": "Urban",
    })

    assert 0 <= result["prob_default"] <= 1
    assert result["decision"] in {"APPROVED", "REJECTED"}
    assert set(result["shap"]) == set(oracle.features)


def test_bundled_artifacts_and_dataset_exist():
    for path in (
        "data/npa_risk_model.json",
        "data/feature_names.json",
        "data/label_encoders.joblib",
        "data/msme_dataset.csv",
        "data/simulation_history.db",
    ):
        assert Path(path).exists()
