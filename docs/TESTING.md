# Testing checklist

Run from the project root after installing requirements:

```bash
python -m pytest -q
```

For a quick manual smoke test:

```bash
python scripts/bootstrap.py
python scripts/run_sim.py --months 2 --no-llm
streamlit run frontend/app.py
```

Check that the oracle can load the bundled artifacts, a short simulation completes, new log rows appear in `data/simulation.db`, and the dashboard displays both the new run and the separate imported history. The historical database should not be used as the write target for a new run.

## Groq integration checks

The automated tests use mocked responses, so they do not need an API key and do not make network calls. They check that both agents parse valid JSON, mark accepted responses as `Groq`, and fall back when a response is malformed. After adding your own key to `.env`, use `python scripts/run_sim.py --months 2` and check the dashboard's **Agent decisions** tab for the `source` column. A live API check has not been run as part of packaging because it requires your private key and account access.
