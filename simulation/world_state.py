"""Stores the main economic values that are shared across the simulation."""

from dataclasses import dataclass, asdict, field

@dataclass
class WorldState:
    """Holds the current economic conditions and active stress scenarios."""
    month: int = 0
    gdp_growth_pct: float = 6.5
    cpi_inflation_pct: float = 4.8
    rbi_repo_rate_pct: float = 6.5
    inr_usd_rate: float = 83.5
    avg_npa_pct: float = 3.2
    total_credit_outstanding: float = 1_800_000.0
    interbank_liquidity: float = 100.0
    shock_monsoon: bool = False
    shock_nbfc: bool = False
    shock_fii: bool = False
    shock_yes_bank: bool = False
    rbi_last_reasoning: str = "Simulation initialized."
    msme_default_rate_pct: float = 0.0
    consumer_default_rate_pct: float = 0.0
    _shock_months: dict = field(default_factory=dict, repr=False)

    def active_shocks(self):
        mapping = [
            ("MONSOON_DEFICIT", self.shock_monsoon),
            ("NBFC_CRISIS", self.shock_nbfc),
            ("FII_PULLOUT", self.shock_fii),
            ("YES_BANK_SPIRAL", self.shock_yes_bank),
        ]
        return [name for name, active in mapping if active]

    def summary_prompt(self):
        return (
            f"Month {self.month}; GDP growth {self.gdp_growth_pct:.2f}%; "
            f"CPI inflation {self.cpi_inflation_pct:.2f}%; repo rate "
            f"{self.rbi_repo_rate_pct:.2f}%; INR/USD {self.inr_usd_rate:.2f}; "
            f"system NPA {self.avg_npa_pct:.2f}%; interbank liquidity "
            f"{self.interbank_liquidity:.1f}; active shocks: "
            f"{', '.join(self.active_shocks()) or 'none'}."
        )

    def to_dict(self):
        d = asdict(self)
        d.pop("_shock_months", None)
        d["active_shocks"] = self.active_shocks()
        return d
