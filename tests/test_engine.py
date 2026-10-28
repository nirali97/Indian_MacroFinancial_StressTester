"""Checks the main simulation behaviour using small test cases."""

import pytest
from simulation.engine import SimulationEngine
from simulation.world_state import WorldState

@pytest.fixture
def engine(tmp_path):
    """Creates a small simulation for use in the tests."""
    return SimulationEngine(n_banks=2,n_msmes=20,n_consumers=50,db_path=str(tmp_path/"test.db"),seed=1)

def test_step_increments_month(engine):
    """Checks that step increments month."""
    engine.step()
    assert engine.world_state.month == 1

def test_double_entry_ledger(engine):
    """Checks that double entry ledger."""
    bank, msme = engine.banks[0], engine.msmes[0]
    b0, m0 = bank.cash_reserves, msme.cash_reserves
    assert engine.ledger.transfer(bank, msme, 100, "TEST", 1)
    assert bank.cash_reserves == pytest.approx(b0-100)
    assert msme.cash_reserves == pytest.approx(m0+100)

def test_insufficient_funds_blocked(engine):
    """Checks that insufficient funds blocked."""
    bank, msme = engine.banks[0], engine.msmes[0]
    bank.cash_reserves = 5
    assert engine.ledger.transfer(bank, msme, 50, "TEST", 1) is False

def test_shock_toggles(engine):
    """Checks that shock toggles."""
    engine.trigger_shock("MONSOON_DEFICIT")
    assert engine.world_state.shock_monsoon
    engine.clear_shock("MONSOON_DEFICIT")
    assert not engine.world_state.shock_monsoon

def test_npa_bounds(engine):
    """Checks that npa bounds."""
    for _ in range(3): engine.step()
    assert all(0 <= b.npa_ratio <= 100 for b in engine.banks)

def test_world_state_serialisable():
    """Checks that world state serialisable."""
    state = WorldState()
    assert "month" in state.to_dict()
    assert "gdp_growth_pct" in state.to_dict()

def test_reset_preserves_population_sizes(engine):
    """Checks that reset preserves population sizes."""
    engine.step()
    engine.reset()
    assert engine.world_state.month == 0
    assert len(engine.msmes) == 20
    assert len(engine.consumers) == 50

def test_nbfc_reduces_liquidity(engine):
    """Checks that nbfc reduces liquidity."""
    initial = engine.world_state.interbank_liquidity
    engine.trigger_shock("NBFC_CRISIS")
    engine.step()
    assert engine.world_state.interbank_liquidity < initial
