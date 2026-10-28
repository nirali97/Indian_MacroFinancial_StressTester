"""Creates a synthetic MSME dataset for training and testing the credit-risk model."""

from pathlib import Path
import numpy as np
import pandas as pd

SECTORS = ["Manufacturing", "Retail", "Agriculture", "Services", "Construction"]
REGIONS = ["Urban", "Rural", "Semi-Urban"]

def generate_dataset(n=100_000, output="data/msme_dataset.csv", seed=42):
    """Creates sample MSME records and synthetic default labels."""
    rng = np.random.default_rng(seed)
    revenue = rng.uniform(1200, 24000, n)
    cibil = np.clip(rng.normal(690, 75, n), 300, 900)
    debt = rng.uniform(0, 0.4, n) * revenue
    import_dep = rng.binomial(1, 0.22, n)
    employees = rng.integers(1, 251, n)
    years = rng.integers(1, 31, n)
    fixed = rng.uniform(50, 300, n)
    sector = rng.choice(SECTORS, n)
    region = rng.choice(REGIONS, n)
    logit = (
        -2.0
        + np.maximum(0, 650-cibil)/100 * 0.65
        + (debt / np.maximum(revenue, 1)) * 2.2
        + (region == "Rural") * 0.35
        + (sector == "Agriculture") * 0.35
        + import_dep * 0.35
        + (revenue < 5000) * 0.25
        + (years < 3) * 0.25
    )
    prob = np.clip(1 / (1 + np.exp(-logit)), 0.01, 0.95)
    defaulted = rng.binomial(1, prob)
    df = pd.DataFrame({
        "annual_revenue": revenue.round(2), "cibil_score": cibil.round().astype(int),
        "existing_debt": debt.round(2), "import_dependent": import_dep,
        "employee_count": employees, "years_in_business": years,
        "fixed_costs_monthly": fixed.round(2), "sector": sector, "region": region,
        "defaulted": defaulted
    })
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    return df

if __name__ == "__main__":
    df = generate_dataset()
    print(f"Wrote {len(df):,} synthetic MSME records; default rate={df.defaulted.mean():.1%}")
