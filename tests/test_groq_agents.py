"""Checks the LLM agents without making real network calls or using an API key."""

from types import SimpleNamespace

from agents.bank_ceo import BankCEOAgent
from agents.rbi_governor import RBIGovernorAgent
from simulation.world_state import WorldState


class FakeCompletions:
    """Return a small pretend Groq response for repeatable tests."""

    def __init__(self, content):
        self.content = content
        self.last_request = None

    def create(self, **kwargs):
        self.last_request = kwargs
        message = SimpleNamespace(content=self.content)
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])


class FakeGroq:
    def __init__(self, content):
        self.completions = FakeCompletions(content)
        self.chat = SimpleNamespace(completions=self.completions)


def test_rbi_agent_marks_groq_decision():
    client = FakeGroq('{"new_repo_rate": 6.25, "reasoning": "Inflation is above target."}')
    result = RBIGovernorAgent(client=client, model="test-model").decide(WorldState())
    assert result["new_repo_rate"] == 6.25
    assert result["source"] == "Groq"
    assert client.completions.last_request["model"] == "test-model"


def test_bank_agent_marks_groq_decision():
    client = FakeGroq('{"risk_appetite":"conservative","max_loan_pct_of_capital":0.08,"reasoning":"Credit risk is high."}')
    agent = BankCEOAgent("SBI", client=client, model="test-model")
    result = agent.decide_strategy(WorldState(), 11.0)
    assert result["risk_appetite"] == "conservative"
    assert result["max_loan_pct_of_capital"] == 0.08
    assert result["source"] == "Groq"


def test_rbi_agent_uses_fallback_when_groq_returns_bad_json():
    result = RBIGovernorAgent(client=FakeGroq("not json")).decide(WorldState())
    assert result["source"] == "Rule-based fallback"
    assert 3.0 <= result["new_repo_rate"] <= 10.0


def test_bank_agent_uses_fallback_without_client():
    result = BankCEOAgent("SBI", client=None, enabled=False).decide_strategy(WorldState(), 12.0)
    assert result["source"] == "Rule-based fallback"
    assert result["risk_appetite"] == "conservative"
