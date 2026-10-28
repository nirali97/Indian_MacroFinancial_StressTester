# Architecture and data flow

```text
Streamlit dashboard / command-line runner
                |
                v
        SimulationEngine.step()
          /      |       \
         v       v        v
      Shocks   Policy agents   Loan Oracle
         |       |               |
         v       v               v
     WorldState Groq or rules   XGBoost + encoders
          \       |               /
           \      v              /
              Ledger and SQLite logs
```

The diagram is conceptual. The engine owns the monthly sequence and calls each component. `WorldState` holds shared macro indicators, the agents represent simulated participants/policy roles, the oracle provides a default-risk estimate, and SQLite stores logs. The ledger records simulated money transfers.

## Main data path

1. An MSME's attributes are collected into a dictionary.
2. `LoanOracle` encodes sector and region and arranges all nine values in the model's saved feature order.
3. XGBoost returns a class-1 probability.
4. The engine compares it with a threshold adjusted by the bank's strategy.
5. The decision and explanation are logged; approved loans may trigger a ledger transfer.

The model's probability is only one input in this illustrative simulation. It is not a real creditworthiness determination.

## Policy-agent path

The RBI Governor and each Bank CEO agent try Groq when `GROQ_API_KEY` is configured. `GROQ_MODEL` chooses the model. The agents validate and bound the returned values before the simulation uses them. If the key is missing, the request fails, or the response cannot be parsed, the agent uses local rules instead. The database records the decision source so the dashboard can distinguish a Groq response from a fallback. `--no-llm` disables Groq calls for both types of policy agent.
