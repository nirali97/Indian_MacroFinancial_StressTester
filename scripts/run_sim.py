"""Runs the simulation from the terminal without opening the dashboard."""

import argparse
from simulation.engine import SimulationEngine
from agents.rbi_governor import RBIGovernorAgent
from ml.oracle import LoanOracle

def main():
    """Reads the command-line options and runs the simulation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--months", type=int, default=12)
    parser.add_argument("--shock", choices=["MONSOON_DEFICIT","NBFC_CRISIS","FII_PULLOUT","YES_BANK_SPIRAL"])
    parser.add_argument("--no-ml", action="store_true")
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args()
    try:
        oracle = None if args.no_ml else LoanOracle()
    except Exception as e:
        print(f"ML oracle disabled: {e}")
        oracle = None
    rbi = None if args.no_llm else RBIGovernorAgent()
    engine = SimulationEngine(ml_oracle=oracle, rbi_agent=rbi, use_llm=not args.no_llm)
    if args.shock:
        engine.trigger_shock(args.shock)
    for _ in range(args.months):
        ws = engine.step()
        print(f"M{ws.month:03d} GDP={ws.gdp_growth_pct:.2f}% CPI={ws.cpi_inflation_pct:.2f}% "
              f"Repo={ws.rbi_repo_rate_pct:.2f}% NPA={ws.avg_npa_pct:.2f}% "
              f"MSME defaults={ws.msme_default_rate_pct:.1f}% liquidity={ws.interbank_liquidity:.1f}")
if __name__ == "__main__":
    main()
