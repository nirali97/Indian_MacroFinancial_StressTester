"""Applies the changes caused by the selected economic stress scenarios."""

def apply_shocks(world_state, banks):
    """Apply one month's macro impact; no direct fake NPA overrides."""
    ws = world_state
    if ws.shock_monsoon:
        ws.gdp_growth_pct -= 0.12
        ws.cpi_inflation_pct += 0.08
    if ws.shock_nbfc:
        ws.interbank_liquidity = max(10.0, ws.interbank_liquidity - 3.0)
        ws.gdp_growth_pct -= 0.08
    if ws.shock_fii:
        ws.inr_usd_rate += 0.45
        ws.cpi_inflation_pct += 0.10
        ws.gdp_growth_pct -= 0.06
    if ws.shock_yes_bank:
        ws.interbank_liquidity = max(10.0, ws.interbank_liquidity - 2.0)
        ws.gdp_growth_pct -= 0.05
        if banks:
            target = max(banks, key=lambda b: b.npa_ratio)
            # Liquidity stress is an explicit cash loss once per active month.
            target.cash_reserves = max(0.0, target.cash_reserves * 0.99)
    if not ws.active_shocks():
        ws.gdp_growth_pct += (6.5 - ws.gdp_growth_pct) * 0.08
        ws.cpi_inflation_pct += (4.8 - ws.cpi_inflation_pct) * 0.08
        ws.inr_usd_rate += (83.5 - ws.inr_usd_rate) * 0.05
        ws.interbank_liquidity += (100.0 - ws.interbank_liquidity) * 0.08
    ws.gdp_growth_pct = max(-5.0, min(12.0, ws.gdp_growth_pct))
    ws.cpi_inflation_pct = max(0.0, min(20.0, ws.cpi_inflation_pct))
