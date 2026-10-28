"""Choose a simulated bank's lending posture using Groq or simple rules."""

import json
import re

from agents.groq_setup import get_groq_client, get_groq_model
from simulation.world_state import WorldState

SYSTEM_PROMPT = """You are a commercial bank CEO in an educational simulation.
Return only JSON with this shape:
{"risk_appetite":"conservative|moderate|aggressive",
"max_loan_pct_of_capital": number from 0.05 to 0.20,
"reasoning":"one short sentence"}.
Consider the bank's NPA ratio, economy and active shocks. Do not claim this is real bank policy."""


class BankCEOAgent:
    """Choose how cautious a bank should be when giving new loans."""

    def __init__(self, bank_name, api_key=None, model=None, client=None, enabled=True):
        self.bank_name = bank_name
        self.client = (client or (get_groq_client() if api_key is None else self._make_client(api_key))) if enabled else None
        self.model = model or get_groq_model()
        self.current_strategy = {
            "risk_appetite": "moderate",
            "max_loan_pct_of_capital": 0.10,
            "reasoning": "Initial strategy.",
            "source": "Initial setting",
        }
        self.last_error = ""

    @staticmethod
    def _make_client(api_key):
        try:
            from groq import Groq
            return Groq(api_key=api_key, timeout=20.0, max_retries=1) if api_key else None
        except ImportError:
            return None

    def decide_strategy(self, world_state: WorldState, bank_npa: float):
        """Get a lending strategy for this bank, then check its values before use."""
        result = None
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": (
                            f"{world_state.summary_prompt()} Bank: {self.bank_name}. "
                            f"Bank NPA ratio: {bank_npa:.2f}%. Return valid JSON only."
                        )},
                    ],
                    temperature=0.2,
                    max_tokens=300,
                    reasoning_effort="low",
                    response_format={"type": "json_object"},
                )
                raw = response.choices[0].message.content or "{}"
                answer = json.loads(re.sub(r"```(?:json)?|```", "", raw).strip())
                appetite = str(answer.get("risk_appetite", "moderate")).lower()
                if appetite not in {"conservative", "moderate", "aggressive"}:
                    appetite = "moderate"
                pct = max(0.05, min(0.20, float(answer.get("max_loan_pct_of_capital", 0.10))))
                result = {
                    "risk_appetite": appetite,
                    "max_loan_pct_of_capital": pct,
                    "reasoning": str(answer.get("reasoning", "Groq suggested this strategy.")),
                    "source": "Groq",
                }
                self.last_error = ""
            except Exception as exc:
                self.last_error = f"{type(exc).__name__}: {exc}"[:300]

        if result is None:
            result = self._use_simple_rule(world_state, bank_npa)
            if not self.client:
                self.last_error = "GROQ_API_KEY is missing or the Groq package is unavailable."

        self.current_strategy = result.copy()
        return result

    @staticmethod
    def _use_simple_rule(world_state, bank_npa):
        """Use clear rules as a backup so a network issue cannot stop the simulation."""
        if bank_npa > 10 or world_state.shock_nbfc or world_state.shock_yes_bank:
            appetite, pct = "conservative", 0.05
        elif bank_npa > 6 or world_state.avg_npa_pct > 7:
            appetite, pct = "moderate", 0.10
        else:
            appetite, pct = "aggressive", 0.18
        return {
            "risk_appetite": appetite,
            "max_loan_pct_of_capital": pct,
            "reasoning": f"Rule-based fallback: NPA is {bank_npa:.1f}%; {appetite} lending posture.",
            "source": "Rule-based fallback",
        }
