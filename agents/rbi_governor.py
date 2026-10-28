"""Suggest a repo rate from the current economy, using Groq when configured."""

import json
import re

from agents.groq_setup import get_groq_client, get_groq_model
from simulation.world_state import WorldState

SYSTEM_PROMPT = """You are the RBI Governor in an educational macro-financial simulation.
Return only JSON with this shape:
{"new_repo_rate": number from 3 to 10, "reasoning": "one short sentence"}.
Consider inflation, growth, banking stress and active shocks. Do not claim this is real RBI policy."""


class RBIGovernorAgent:
    """Pick a simulated repo rate and keep track of where the decision came from."""

    def __init__(self, api_key=None, model=None, client=None, enabled=True):
        # A client can be passed directly in tests; otherwise I read the local settings.
        self.client = (client or (get_groq_client() if api_key is None else self._make_client(api_key))) if enabled else None
        self.model = model or get_groq_model()
        self.decision_history = []
        self.last_error = ""

    @staticmethod
    def _make_client(api_key):
        try:
            from groq import Groq
            return Groq(api_key=api_key, timeout=20.0, max_retries=1) if api_key else None
        except ImportError:
            return None

    def decide(self, world_state: WorldState):
        """Ask Groq for a rate first; use the simple formula if the call fails."""
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": (
                            f"{world_state.summary_prompt()} Current repo rate: "
                            f"{world_state.rbi_repo_rate_pct:.2f}%. Return valid JSON only."
                        )},
                    ],
                    temperature=0.2,
                    max_tokens=300,
                    reasoning_effort="low",
                    response_format={"type": "json_object"},
                )
                raw = response.choices[0].message.content or "{}"
                answer = json.loads(re.sub(r"```(?:json)?|```", "", raw).strip())
                rate = max(3.0, min(10.0, float(answer["new_repo_rate"])))
                result = {
                    "new_repo_rate": rate,
                    "reasoning": str(answer.get("reasoning", "Groq suggested a rate.")),
                    "source": "Groq",
                }
                self.last_error = ""
            except Exception as exc:
                # I save the error so the dashboard can show when the fallback was used.
                self.last_error = f"{type(exc).__name__}: {exc}"[:300]
                result = self._use_simple_rule(world_state)
        else:
            self.last_error = "GROQ_API_KEY is missing or the Groq package is unavailable."
            result = self._use_simple_rule(world_state)

        self.decision_history.append(result.copy())
        return result

    @staticmethod
    def _use_simple_rule(world_state):
        """Keep the simulation running when the external API is unavailable."""
        inflation_gap = world_state.cpi_inflation_pct - 4.0
        growth_gap = world_state.gdp_growth_pct - 6.0
        rate = 5.5 + 0.5 * inflation_gap - 0.5 * growth_gap
        if world_state.shock_fii:
            rate += 0.25
        if world_state.shock_nbfc or world_state.shock_yes_bank:
            rate -= 0.25
        rate = round(max(3.0, min(10.0, rate)), 2)
        return {
            "new_repo_rate": rate,
            "reasoning": (
                f"Rule-based fallback: inflation {world_state.cpi_inflation_pct:.1f}%, "
                f"growth {world_state.gdp_growth_pct:.1f}%, NPA {world_state.avg_npa_pct:.1f}%."
            ),
            "source": "Rule-based fallback",
        }
